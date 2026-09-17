"""Initial migration with pgvector

Revision ID: 001_initial
Revises: 
Create Date: 2026-09-17 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
import pgvector

revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # 2. Users table
    op.create_table(
        'users',
        sa.Column('id', sa.UUID(), nullable=False, primary_key=True),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # 3. Documents table
    op.create_table(
        'documents',
        sa.Column('id', sa.UUID(), nullable=False, primary_key=True),
        sa.Column('user_id', sa.UUID(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=512), nullable=False),
        sa.Column('file_type', sa.String(length=50), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='UPLOADED'),
        sa.Column('error_message', sa.String(length=1024), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f('ix_documents_user_id'), 'documents', ['user_id'], unique=False)
    op.create_index(op.f('ix_documents_status'), 'documents', ['status'], unique=False)

    # 4. Document Chunks table (with pgvector)
    op.create_table(
        'document_chunks',
        sa.Column('id', sa.UUID(), nullable=False, primary_key=True),
        sa.Column('document_id', sa.UUID(), sa.ForeignKey('documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.UUID(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('embedding', pgvector.sqlalchemy.Vector(384), nullable=True),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('page_number', sa.Integer(), nullable=True),
        sa.Column('section', sa.String(length=255), nullable=True),
        sa.Column('token_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('metadata', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f('ix_document_chunks_document_id'), 'document_chunks', ['document_id'], unique=False)
    op.create_index(op.f('ix_document_chunks_user_id'), 'document_chunks', ['user_id'], unique=False)

    # HNSW Cosine Similarity Index on vector embedding
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_document_chunks_embedding ON document_chunks USING hnsw (embedding vector_cosine_ops);"
    )

    # 5. Conversations table
    op.create_table(
        'conversations',
        sa.Column('id', sa.UUID(), nullable=False, primary_key=True),
        sa.Column('user_id', sa.UUID(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False, server_default='New Conversation'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f('ix_conversations_user_id'), 'conversations', ['user_id'], unique=False)

    # 6. Messages table
    op.create_table(
        'messages',
        sa.Column('id', sa.UUID(), nullable=False, primary_key=True),
        sa.Column('conversation_id', sa.UUID(), sa.ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('citations', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f('ix_messages_conversation_id'), 'messages', ['conversation_id'], unique=False)

    # 7. Retrieval Logs table
    op.create_table(
        'retrieval_logs',
        sa.Column('id', sa.UUID(), nullable=False, primary_key=True),
        sa.Column('conversation_id', sa.UUID(), sa.ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('query', sa.String(length=1024), nullable=False),
        sa.Column('retrieved_chunk_ids', sa.JSON(), nullable=False),
        sa.Column('latency_ms', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f('ix_retrieval_logs_conversation_id'), 'retrieval_logs', ['conversation_id'], unique=False)


def downgrade() -> None:
    op.drop_table('retrieval_logs')
    op.drop_table('messages')
    op.drop_table('conversations')
    op.execute("DROP INDEX IF EXISTS ix_document_chunks_embedding;")
    op.drop_table('document_chunks')
    op.drop_table('documents')
    op.drop_table('users')
