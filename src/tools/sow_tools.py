"""
SOW Tools — parse SOW documents and extract key concepts.
"""

import io
import re
from pathlib import Path

from src.app import mcp
from src.state import state


@mcp.tool()
async def parse_sow(content: str, filename: str = "input.txt") -> dict:
    """
    Parse a Statement of Work document and extract text + key concepts.

    Args:
        content: The raw text content of the SOW (or base64 for binary files).
                 For text/paste, just pass the SOW text directly.
        filename: Original filename to detect format (e.g., "sow.pdf", "sow.docx").
                  Defaults to "input.txt" for pasted text.

    Returns:
        Dictionary with extracted text, concepts, entities, and modules mentioned.
    """
    ext = Path(filename).suffix.lower()

    # For plain text input (most common — user pastes SOW in chat)
    if ext in (".txt", "") or not ext:
        text = content
    elif ext == ".pdf":
        import base64
        raw_bytes = base64.b64decode(content)
        text = _parse_pdf(raw_bytes)
    elif ext in (".docx", ".doc"):
        import base64
        raw_bytes = base64.b64decode(content)
        text = _parse_docx(raw_bytes)
    else:
        text = content

    # Extract key concepts from the SOW text
    concepts = _extract_concepts(text)

    # Cache in state
    state.last_sow_text = text
    state.last_concepts = concepts

    return {
        "text": text[:5000],  # First 5000 chars for context window
        "full_length": len(text),
        "concepts": concepts,
        "entities": _extract_entities(text),
        "modules_mentioned": _extract_modules(text),
    }


def _parse_pdf(content: bytes) -> str:
    """Extract text from PDF bytes."""
    import PyPDF2
    reader = PyPDF2.PdfReader(io.BytesIO(content))
    text_parts = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            text_parts.append(text)
    return "\n".join(text_parts)


def _parse_docx(content: bytes) -> str:
    """Extract text from DOCX bytes."""
    import docx
    doc = docx.Document(io.BytesIO(content))
    return "\n".join(para.text for para in doc.paragraphs if para.text.strip())


def _extract_concepts(text: str) -> list[str]:
    """
    Extract key business concepts from SOW text.
    Uses keyword patterns common in legal/ops SOWs.
    """
    concepts = []

    # Look for section headers (common patterns in SOWs)
    header_patterns = [
        r"(?:^|\n)\d+\.\d*\s*(.+?)(?:\n|$)",  # "1.1 Feature Name"
        r"(?:^|\n)#{1,3}\s*(.+?)(?:\n|$)",  # "## Feature Name"
        r"(?:^|\n)(?:Feature|Requirement|Module|Capability):\s*(.+?)(?:\n|$)",
    ]
    for pattern in header_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        concepts.extend(m.strip() for m in matches if len(m.strip()) > 3)

    # Look for key phrases that indicate requirements
    requirement_indicators = [
        r"(?:shall|must|should|will)\s+(?:be able to|provide|support|enable|allow)\s+(.+?)(?:\.|$)",
    ]
    for pattern in requirement_indicators:
        matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
        concepts.extend(m.strip()[:100] for m in matches if len(m.strip()) > 5)

    # Deduplicate while preserving order
    seen = set()
    unique = []
    for c in concepts:
        lower = c.lower()
        if lower not in seen:
            seen.add(lower)
            unique.append(c)

    return unique[:30]  # Cap at 30 concepts


def _extract_entities(text: str) -> list[str]:
    """Extract likely Passport entity names from SOW text."""
    # Common Passport entities
    known_entities = [
        "matter", "client", "timekeeper", "invoice", "budget", "accrual",
        "vendor", "rate", "approval", "workflow", "document", "report",
        "user", "role", "permission", "notification", "email", "template",
        "rule", "condition", "action", "schedule", "task", "alert",
    ]
    text_lower = text.lower()
    return [e for e in known_entities if e in text_lower]


def _extract_modules(text: str) -> list[str]:
    """Extract likely Passport module names from SOW text."""
    known_modules = [
        "eBilling", "Matter Management", "Spend Management", "Budgeting",
        "Accruals", "Rate Management", "Appeals", "Analytics", "Reporting",
        "Workflow", "Document Management", "Vendor Management", "Timekeeper",
        "Legal Hold", "Outside Counsel", "Invoice Review", "Compliance",
    ]
    text_lower = text.lower()
    return [m for m in known_modules if m.lower() in text_lower]
