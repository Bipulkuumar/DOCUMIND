import asyncio
import json
import os
import sys
import uuid
from typing import List, Dict, Any

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.db.base import Base
from app.models.user import User
from app.models.document import Document
from app.services.ingestion_service import IngestionService
from app.services.rag_service import RAGService
from app.ai.providers.embeddings import MockEmbeddingProvider
from app.ai.providers.llm import MockLLMProvider
from app.services.embedding_service import EmbeddingService


async def run_evaluation():
    print("=" * 70)
    print("           DocuMind — RAG Pipeline Offline Evaluation Engine          ")
    print("=" * 70)

    # 1. Setup in-memory SQLite database for evaluation
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    SessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with SessionLocal() as db:
        # 2. Create Evaluation Test User
        eval_user = User(
            id=uuid.uuid4(),
            email="evaluator@documind.ai",
            hashed_password="dummy_hashed_password",
            full_name="RAG Evaluator"
        )
        db.add(eval_user)
        await db.commit()
        await db.refresh(eval_user)

        # 3. Ingest Sample Documents
        sample_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "sample_data"))
        sample_files = ["company_policy.md", "product_manual.txt"]

        print("\n[+] Ingesting Sample Evaluation Corpus:")
        ingestion_service = IngestionService(
            db,
            embedding_service=EmbeddingService(provider=MockEmbeddingProvider(dim=384))
        )

        for fname in sample_files:
            fpath = os.path.join(sample_dir, fname)
            ext = os.path.splitext(fname)[1].lstrip(".")
            file_size = os.path.getsize(fpath)

            doc = Document(
                id=uuid.uuid4(),
                user_id=eval_user.id,
                filename=fname,
                file_path=fpath,
                file_type=ext,
                file_size=file_size,
                status="UPLOADED",
                doc_metadata={"eval_sample": True}
            )
            db.add(doc)
            await db.commit()
            await db.refresh(doc)

            ok = await ingestion_service.process_document(doc.id, eval_user.id)
            print(f"  - Ingested '{fname}': {'SUCCESS' if ok else 'FAILED'}")

        # 4. Load Evaluation Dataset
        dataset_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "evaluation", "questions.json"))
        with open(dataset_path, "r", encoding="utf-8") as f:
            questions = json.load(f)

        rag_service = RAGService(
            db,
            llm_provider=MockLLMProvider(),
            retrieval_service=None
        )

        # 5. Evaluate Questions
        total_q = len(questions)
        hit_count = 0
        grounded_count = 0
        citation_correct_count = 0
        relevance_scores: List[float] = []

        eval_records: List[Dict[str, Any]] = []

        print(f"\n[+] Executing RAG Evaluation Suite ({total_q} test questions):")
        print("-" * 70)

        for q in questions:
            q_id = q["id"]
            query = q["question"]
            exp_doc = q["expected_document"]
            exp_keywords = q["expected_answer_keywords"]
            is_unrelated = q["unrelated"]

            rag_res = await rag_service.answer_question(
                query=query,
                user_id=eval_user.id,
                top_k=5,
                similarity_threshold=0.0
            )

            # Measure Hit@K
            retrieved_docs = [r.document_name for r in rag_res.search_results]
            hit = False
            if is_unrelated:
                hit = (len(rag_res.search_results) == 0) or ("couldn't find" in rag_res.answer.lower())
            else:
                hit = exp_doc in retrieved_docs if exp_doc else False

            if hit:
                hit_count += 1

            # Measure Groundedness
            ans_lower = rag_res.answer.lower()
            grounded = any(kw.lower() in ans_lower for kw in exp_keywords)
            if grounded:
                grounded_count += 1

            # Measure Citation Correctness
            cit_correct = False
            if is_unrelated:
                cit_correct = (len(rag_res.citations) == 0)
            else:
                cit_docs = [c["document_name"] for c in rag_res.citations]
                cit_correct = exp_doc in cit_docs if exp_doc else False

            if cit_correct:
                citation_correct_count += 1

            # Average Top Similarity
            top_sim = rag_res.search_results[0].similarity if rag_res.search_results else 0.0
            relevance_scores.append(top_sim)

            eval_records.append({
                "id": q_id,
                "question": query,
                "hit": hit,
                "grounded": grounded,
                "citation_correct": cit_correct,
                "top_similarity": top_sim,
                "answer": rag_res.answer,
                "citations_count": len(rag_res.citations)
            })

            status_str = "PASS" if (hit and grounded) else "PARTIAL/FAIL"
            print(f"[{status_str}] QID: {q_id} | '{query[:45]}...' | Hit: {hit} | Grounded: {grounded}")

        # 6. Aggregate Evaluation Metrics
        hit_at_k = (hit_count / total_q) * 100.0
        answer_groundedness = (grounded_count / total_q) * 100.0
        citation_accuracy = (citation_correct_count / total_q) * 100.0
        avg_context_relevance = (sum(relevance_scores) / len(relevance_scores)) if relevance_scores else 0.0

        summary = {
            "total_questions": total_q,
            "retrieval_hit_at_k_pct": round(hit_at_k, 2),
            "answer_groundedness_pct": round(answer_groundedness, 2),
            "citation_accuracy_pct": round(citation_accuracy, 2),
            "avg_context_relevance": round(avg_context_relevance, 4),
            "details": eval_records
        }

        print("\n" + "=" * 70)
        print("                        FINAL EVALUATION SUMMARY                      ")
        print("=" * 70)
        print(f"  Retrieval Hit@K Metric   :  {hit_at_k:.1f}%")
        print(f"  Answer Groundedness      :  {answer_groundedness:.1f}%")
        print(f"  Citation Accuracy        :  {citation_accuracy:.1f}%")
        print(f"  Avg Context Similarity   :  {avg_context_relevance:.4f}")
        print("=" * 70)

        output_json_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "evaluation", "eval_results.json"))
        with open(output_json_path, "w", encoding="utf-8") as out:
            json.dump(summary, out, indent=2)

        print(f"\n[+] Detailed evaluation report saved to: [eval_results.json]({output_json_path})")


if __name__ == "__main__":
    asyncio.run(run_evaluation())
