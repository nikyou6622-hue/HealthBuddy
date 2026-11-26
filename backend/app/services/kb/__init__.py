"""Unified Knowledge Base record builder for hospitals, doctors, guidance, and care."""

from app.services.kb.records import (
    KNOWLEDGE_BASE_JSON_PATH,
    build_knowledge_base_record,
    get_knowledge_base,
)

__all__ = ["KNOWLEDGE_BASE_JSON_PATH", "build_knowledge_base_record", "get_knowledge_base"]

