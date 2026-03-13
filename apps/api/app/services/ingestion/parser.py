from __future__ import annotations

import re
from typing import Any

from pypdf import PdfReader


SECTION_PATTERN = re.compile(
    r"^(?:(\d+(?:\.\d+)*)\s+)?([A-Z][A-Za-z0-9 ,/\-\(\):]{2,})$"
)


def extract_text_by_page(file_path: str) -> list[dict[str, Any]]:
    reader = PdfReader(file_path)
    pages: list[dict[str, Any]] = []
    for index, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        pages.append({"page_num": index, "text": text})
    return pages


def infer_title(pages: list[dict[str, Any]], fallback: str) -> str:
    if not pages:
        return fallback
    first_page_lines = [line.strip() for line in pages[0]["text"].splitlines() if line.strip()]
    for line in first_page_lines[:8]:
        if len(line.split()) >= 3 and len(line) <= 180:
            return line
    return fallback


def infer_abstract(full_text: str) -> str:
    match = re.search(
        r"abstract\s*(.+?)(?:\n\s*\n|\n1\s+[A-Z]|\nI\.\s+[A-Z])",
        full_text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if match:
        return normalize_whitespace(match.group(1))[:1600]
    return normalize_whitespace(full_text)[:800]


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def split_sections(pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sections: list[dict[str, Any]] = []
    current = {
        "section_title": "Introduction",
        "section_path": "Introduction",
        "page_start": 1,
        "page_end": 1,
        "content": [],
    }
    for page in pages:
        lines = [line.strip() for line in page["text"].splitlines() if line.strip()]
        matched_title = None
        for line in lines[:6]:
            match = SECTION_PATTERN.match(line)
            if match and len(line.split()) <= 10:
                matched_title = line
                break
        if matched_title and current["content"]:
            current["page_end"] = max(current["page_end"], page["page_num"] - 1)
            sections.append(current)
            current = {
                "section_title": matched_title,
                "section_path": matched_title,
                "page_start": page["page_num"],
                "page_end": page["page_num"],
                "content": [page["text"]],
            }
        else:
            current["content"].append(page["text"])
            current["page_end"] = page["page_num"]
    if current["content"]:
        sections.append(current)
    for section in sections:
        section["content"] = normalize_whitespace("\n".join(section["content"]))
    return sections


def build_chunks(sections: list[dict[str, Any]]) -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []
    for section_index, section in enumerate(sections):
        paragraphs = [part.strip() for part in re.split(r"\n\s*\n", section["content"]) if part.strip()]
        if not paragraphs:
            paragraphs = [section["content"]]
        for order, paragraph in enumerate(paragraphs[:6]):
            chunk_type = infer_chunk_type(section["section_title"], paragraph)
            chunks.append(
                {
                    "chunk_id": f"chunk-{section_index + 1}-{order + 1}",
                    "section_title": section["section_title"],
                    "section_path": section["section_path"],
                    "page_num": section["page_start"],
                    "chunk_type": chunk_type,
                    "order_in_section": order + 1,
                    "content": paragraph[:1600],
                    "keywords": infer_keywords(paragraph),
                }
            )
    return chunks


def infer_chunk_type(section_title: str, content: str) -> str:
    text = f"{section_title} {content}".lower()
    if "experiment" in text or "result" in text or "ablation" in text:
        return "experiment_finding"
    if "method" in text or "approach" in text or "architecture" in text:
        return "paragraph"
    if "equation" in text or "\\" in text or "loss" in text:
        return "formula"
    if "contribution" in text:
        return "contribution"
    return "paragraph"


def infer_keywords(content: str) -> list[str]:
    words = re.findall(r"[A-Za-z][A-Za-z\-]{3,}", content.lower())
    seen: list[str] = []
    for word in words:
        if word not in seen:
            seen.append(word)
        if len(seen) == 8:
            break
    return seen
