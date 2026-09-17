import io
import uuid
import pytest
from app.services.text_cleaner import TextCleaner
from app.services.chunking_service import ChunkingService
from app.services.extractors.txt_extractor import TXTExtractor
from app.services.extractors.md_extractor import MDExtractor
from app.services.extractors.base import ExtractedChunkContent
from app.services.ingestion_service import IngestionService
from tests.integration.test_documents import get_auth_token



def test_text_cleaner():
    raw = "  Hello \x00 world!\n\n\n\nThis is    a   test.  "
    cleaned = TextCleaner.clean(raw)
    assert cleaned == "Hello world!\n\nThis is a test."


def test_markdown_extractor_sections(tmp_path):
    md_file = tmp_path / "test.md"
    md_file.write_text("# Section One\nContent for section 1.\n\n## Section Two\nContent for section 2.", encoding="utf-8")
    
    extractor = MDExtractor()
    blocks = extractor.extract(str(md_file))
    assert len(blocks) == 2
    assert blocks[0].section == "Section One"
    assert "Content for section 1." in blocks[0].text
    assert blocks[1].section == "Section Two"
    assert "Content for section 2." in blocks[1].text


def test_chunking_service():
    chunker = ChunkingService(target_chunk_tokens=50, overlap_tokens=10)
    doc_id = uuid.uuid4()
    
    long_text = "Word " * 200  # ~200 words
    blocks = [ExtractedChunkContent(text=long_text, section="Test Section", page_number=1)]
    
    chunks = chunker.chunk_extracted_content(doc_id, "test_file.txt", blocks)
    assert len(chunks) > 1
    for chunk in chunks:
        assert chunk.document_id == doc_id
        assert chunk.page_number == 1
        assert chunk.section == "Test Section"
        assert chunk.metadata["source_filename"] == "test_file.txt"


@pytest.mark.asyncio
async def test_end_to_end_ingestion_pipeline(async_client):
    token = await get_auth_token(async_client, "ingest_user@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # Upload Markdown file
    md_content = b"# Document Title\nThis is paragraph one.\n\n## Subheading\nThis is paragraph two with more details."
    files = {"file": ("manual.md", io.BytesIO(md_content), "text/markdown")}
    
    upload_res = await async_client.post("/api/v1/documents/upload", headers=headers, files=files)
    assert upload_res.status_code == 201
    doc_id = upload_res.json()["data"]["id"]

    # Verify background processing transitions document to READY and creates chunks
    doc_res = await async_client.get(f"/api/v1/documents/{doc_id}", headers=headers)
    assert doc_res.status_code == 200
    assert doc_res.json()["data"]["status"] == "READY"

    # Fetch document chunks
    chunks_res = await async_client.get(f"/api/v1/documents/{doc_id}/chunks", headers=headers)
    assert chunks_res.status_code == 200
    chunk_data = chunks_res.json()["data"]
    assert chunk_data["total_chunks"] >= 1
    first_chunk = chunk_data["chunks"][0]
    assert "Document Title" in first_chunk["content"] or "paragraph" in first_chunk["content"]
