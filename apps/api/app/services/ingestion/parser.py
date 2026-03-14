from __future__ import annotations

import re
from typing import Any

try:
    from pypdf import PdfReader
except ImportError:  # pragma: no cover - exercised in environments without PDF parsing deps
    PdfReader = None


SECTION_PATTERN = re.compile(
    r"^(?:(\d+(?:\.\d+)*)\s+)?([A-Z][A-Za-z0-9 ,/\-\(\):]{2,})$"
)

TITLE_EXCLUDED_PATTERNS = [
    re.compile(pattern, flags=re.IGNORECASE)
    for pattern in [
        r"^published as\b",
        r"^under review\b",
        r"^preprint\b",
        r"^anonymous authors?\b",
        r"^anonymous submission\b",
        r"^proceedings of\b",
        r"^arxiv(?::|\s)",
        r"^openreview\b",
        r"^iclr\b",
        r"^neurips\b",
        r"^icml\b",
        r"^cvpr\b",
        r"^aaai\b",
        r"^acl\b",
        r"^copyright\b",
        r"^page \d+\b",
        r"^\d+\s*/\s*\d+$",
    ]
]

AUTHOR_HINT_PATTERNS = [
    re.compile(pattern, flags=re.IGNORECASE)
    for pattern in [
        r"@",
        r"\b(university|institute|college|school|laboratory|lab|department|faculty|academy|research)\b",
        r"\b(author|authors|affiliation|equal contribution|corresponding)\b",
    ]
]

PERSON_NAME_PATTERN = re.compile(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2}\d*\b")
AUTHOR_FOOTNOTE_PATTERN = re.compile(r"[\*\u2020\u2021\u00a7]")

ABSTRACT_PATTERN = re.compile(r"^abstract\b", flags=re.IGNORECASE)


def extract_text_by_page(file_path: str) -> list[dict[str, Any]]:
    if PdfReader is None:
        raise RuntimeError("pypdf is required for PDF text extraction")
    reader = PdfReader(file_path)
    pages: list[dict[str, Any]] = []
    for index, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        pages.append({"page_num": index, "text": text})
    return pages


def infer_title(pages: list[dict[str, Any]], fallback: str, file_path: str | None = None) -> str:
    if not pages:
        return _metadata_title(file_path) or fallback

    first_page_lines = [line.strip() for line in pages[0]["text"].splitlines() if line.strip()]
    if not first_page_lines:
        return _metadata_title(file_path) or fallback

    search_lines = first_page_lines[:24]
    search_boundary = _infer_title_search_boundary(search_lines)

    candidates: list[tuple[int, str]] = []
    for start in range(search_boundary):
        line = search_lines[start]
        if not _is_title_candidate_line(line):
            continue
        block_lines = [line]
        for next_index in range(start + 1, search_boundary):
            next_line = search_lines[next_index]
            if _is_title_block_boundary_line(next_line):
                break
            if _is_title_continuation_line(next_line):
                block_lines.append(next_line)
                if len(block_lines) == 4:
                    break
                continue
            break
        candidate = normalize_whitespace(" ".join(block_lines))
        score = _score_title_candidate(candidate, start, len(block_lines))
        if score > 0:
            candidates.append((score, candidate))

    if candidates:
        candidates.sort(key=lambda item: item[0], reverse=True)
        best_score, best_candidate = candidates[0]
        if best_score >= 8:
            return best_candidate

    metadata_title = _metadata_title(file_path)
    if metadata_title:
        return metadata_title

    if candidates:
        return candidates[0][1]

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


def _is_title_candidate_line(line: str) -> bool:
    normalized = normalize_whitespace(line)
    if not normalized:
        return False
    if any(pattern.search(normalized) for pattern in TITLE_EXCLUDED_PATTERNS):
        return False
    if ABSTRACT_PATTERN.match(normalized):
        return False
    if _looks_like_author_or_affiliation(normalized):
        return False
    if normalized.endswith("."):
        return False
    if len(normalized) > 220:
        return False
    words = normalized.split()
    if len(words) < 2 or len(words) > 24:
        return False
    if sum(char.isdigit() for char in normalized) > 6:
        return False
    return _looks_like_title(normalized)


def _is_title_continuation_line(line: str) -> bool:
    normalized = normalize_whitespace(line)
    if not normalized:
        return False
    if any(pattern.search(normalized) for pattern in TITLE_EXCLUDED_PATTERNS):
        return False
    if ABSTRACT_PATTERN.match(normalized):
        return False
    if _looks_like_author_or_affiliation(normalized):
        return False
    if len(normalized) > 180:
        return False
    words = normalized.split()
    if len(words) < 2 or len(words) > 18:
        return False
    if normalized.endswith("."):
        return False
    return _looks_like_title(normalized)


def _is_title_block_boundary_line(line: str) -> bool:
    normalized = normalize_whitespace(line)
    if not normalized:
        return True
    if ABSTRACT_PATTERN.match(normalized):
        return True
    if any(pattern.search(normalized) for pattern in TITLE_EXCLUDED_PATTERNS):
        return True
    if _looks_like_author_or_affiliation(normalized):
        return True
    return False


def _infer_title_search_boundary(lines: list[str]) -> int:
    if not lines:
        return 0
    abstract_index = next((index for index, line in enumerate(lines) if ABSTRACT_PATTERN.match(line)), len(lines))
    return max(1, abstract_index if abstract_index != len(lines) else min(len(lines), 24))


def _looks_like_author_or_affiliation(text: str) -> bool:
    if any(pattern.search(text) for pattern in AUTHOR_HINT_PATTERNS):
        return True
    has_author_footnote = bool(AUTHOR_FOOTNOTE_PATTERN.search(text))
    comma_count = text.count(",")
    if comma_count >= 2 and len(text.split()) <= 12:
        return True
    person_like_names = PERSON_NAME_PATTERN.findall(text)
    if len(person_like_names) >= 2 and len(text.split()) <= 18 and (
        comma_count >= 1 or bool(re.search(r"\d", text)) or has_author_footnote
    ):
        return True
    if has_author_footnote and len(person_like_names) >= 1:
        return True
    if len(person_like_names) >= 3 and len(text.split()) <= 18:
        return True
    return False


def _looks_like_title(text: str) -> bool:
    words = [word for word in re.split(r"\s+", text) if word]
    if not words:
        return False
    alpha_words = [word for word in words if re.search(r"[A-Za-z]", word)]
    if not alpha_words:
        return False
    capitalized = 0
    for word in alpha_words:
        cleaned = re.sub(r"^[^A-Za-z]+|[^A-Za-z]+$", "", word)
        if cleaned and cleaned[0].isupper():
            capitalized += 1
    ratio = capitalized / max(1, len(alpha_words))
    return ratio >= 0.35 or ":" in text


def _score_title_candidate(candidate: str, start_index: int, line_count: int = 1) -> int:
    score = 0
    words = candidate.split()
    score += max(0, 10 - start_index)
    score += min(len(words), 12)
    score += min(max(line_count - 1, 0), 2)
    if ":" in candidate or "?" in candidate:
        score += 1
    if any(pattern.search(candidate) for pattern in TITLE_EXCLUDED_PATTERNS):
        score -= 10
    if _looks_like_author_or_affiliation(candidate):
        score -= 20
    if AUTHOR_FOOTNOTE_PATTERN.search(candidate):
        score -= 12
    if candidate.isupper():
        score -= 2
    if candidate.endswith("."):
        score -= 2
    if len(words) < 4:
        score -= 3
    return score


def _metadata_title(file_path: str | None) -> str | None:
    if not file_path or PdfReader is None:
        return None
    try:
        reader = PdfReader(file_path)
        metadata = reader.metadata or {}
        raw_title = metadata.get("/Title") or metadata.get("Title")
    except Exception:
        return None
    if not isinstance(raw_title, str):
        return None
    title = normalize_whitespace(raw_title)
    if not title or any(pattern.search(title) for pattern in TITLE_EXCLUDED_PATTERNS):
        return None
    if _looks_like_author_or_affiliation(title):
        return None
    return title
