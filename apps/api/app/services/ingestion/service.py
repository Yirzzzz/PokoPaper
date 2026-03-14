from __future__ import annotations

from datetime import UTC, datetime
import logging
from pathlib import Path
from uuid import uuid4

from app.repositories.factory import get_repository
from app.services.ingestion.overview_generator import generate_overview
from app.services.ingestion.parser import (
    build_chunks,
    extract_text_by_page,
    infer_abstract,
    infer_title,
    split_sections,
)
from app.services.llm.service import LLMService
from app.services.memory.service import MemoryService
from app.services.paper_entity_memory import PaperEntityMemoryService

logger = logging.getLogger(__name__)


class IngestionService:
    def __init__(self) -> None:
        self.repo = get_repository()
        self.llm_service = LLMService()
        self.memory_service = MemoryService()
        self.paper_entity_memory_service = PaperEntityMemoryService()

    async def upload_and_process(self, filename: str, content: bytes) -> dict:
        now = datetime.now(UTC).isoformat()
        paper_id = f"paper-{uuid4().hex[:8]}"
        job_id = f"job-{uuid4().hex[:8]}"
        file_path = self.repo.save_file(paper_id=paper_id, filename=filename, content=content)
        paper = {
            "id": paper_id,
            "title": Path(filename).stem,
            "authors": ["Unknown"],
            "abstract": "",
            "status": "processing",
            "progress_percent": 5,
            "category": None,
            "tags": [],
            "file_path": file_path,
            "created_at": now,
            "updated_at": now,
        }
        self.repo.upsert_paper(paper)
        self.repo.create_job(
            {
                "job_id": job_id,
                "paper_id": paper_id,
                "status": "processing",
                "stage": "uploaded",
                "progress": 10,
                "created_at": now,
                "updated_at": now,
            }
        )
        self._process_job(job_id=job_id, paper_id=paper_id, file_path=file_path, filename=filename)
        return {"paper_id": paper_id, "job_id": job_id, "status": "processing"}

    def _process_job(self, job_id: str, paper_id: str, file_path: str, filename: str) -> None:
        now = datetime.now(UTC).isoformat()
        logger.info("ingestion.start: paper_id=%s file=%s", paper_id, filename)
        self.repo.update_job(job_id, {"stage": "parsing", "progress": 35, "updated_at": now})
        pages = extract_text_by_page(file_path)
        full_text = "\n\n".join(page["text"] for page in pages if page["text"])
        title = infer_title(pages, fallback=Path(filename).stem, file_path=file_path)
        abstract = infer_abstract(full_text)
        sections = split_sections(pages)
        chunks = build_chunks(sections)
        structure = {
            "paper_id": paper_id,
            "sections": [
                {
                    "section_title": section["section_title"],
                    "section_path": section["section_path"],
                    "page_start": section["page_start"],
                    "page_end": section["page_end"],
                }
                for section in sections
            ],
            "formulas_count": sum(chunk["chunk_type"] == "formula" for chunk in chunks),
            "tables_count": 0,
            "figures_count": 0,
            "chunks": chunks,
        }
        overview = generate_overview(
            paper_id=paper_id,
            title=title,
            abstract=abstract,
            sections=sections,
            chunks=chunks,
        )
        llm_analysis = self.llm_service.generate_structured_analysis(
            title=title,
            abstract=abstract,
            sections=sections,
            chunks=chunks,
        )
        if llm_analysis:
            logger.info("ingestion.analysis: paper_id=%s source=llm", paper_id)
            overview.update(
                {
                    "tldr": llm_analysis.get("tldr", overview["tldr"]),
                    "research_motivation": llm_analysis.get("research_motivation", overview["research_motivation"]),
                    "problem_definition": llm_analysis.get("problem_definition", overview["problem_definition"]),
                    "main_contributions": llm_analysis.get("main_contributions", overview["main_contributions"]),
                    "method_summary": llm_analysis.get("method_summary", overview["method_summary"]),
                    "key_modules": llm_analysis.get("key_modules", overview["key_modules"]),
                    "key_formulas": self._merge_formula_citations(
                        llm_analysis.get("key_formulas", overview["key_formulas"]),
                        overview["key_formulas"][0]["citation"],
                    ),
                    "main_experiments": self._merge_experiment_citations(
                        llm_analysis.get("main_experiments", overview["main_experiments"]),
                        overview["main_experiments"][0]["citation"],
                    ),
                    "limitations": llm_analysis.get("limitations", overview["limitations"]),
                    "prerequisite_knowledge": llm_analysis.get(
                        "prerequisite_knowledge",
                        overview["prerequisite_knowledge"],
                    ),
                    "conclusion": llm_analysis.get("conclusion", overview["conclusion"]),
                    "transferable_insights": llm_analysis.get(
                        "transferable_insights",
                        overview["transferable_insights"],
                    ),
                    "recommended_readings": llm_analysis.get(
                        "recommended_readings",
                        overview["recommended_readings"],
                    ),
                }
            )
        else:
            logger.info("ingestion.analysis: paper_id=%s source=heuristic_fallback", paper_id)
        paper = self.repo.get_paper(paper_id)
        if paper is None:
            raise KeyError(f"paper not found while processing: {paper_id}")
        paper.update(
            {
                "title": title,
                "abstract": abstract,
                "status": "ready",
                "progress_percent": 30,
                "updated_at": now,
            }
        )
        self.repo.upsert_paper(paper)
        self.repo.save_structure(paper_id, structure)
        self.repo.save_overview(paper_id, overview)
        self.paper_entity_memory_service.upsert_from_overview(paper_id=paper_id, overview=overview)
        paper_memory = {
            "scope_type": "paper",
            "scope_id": paper_id,
            "paper_id": paper_id,
            "progress_status": "new",
            "progress_percent": 0,
            "last_read_section": structure["sections"][0]["section_title"] if structure["sections"] else "Unknown",
            "stuck_points": [],
            "key_questions": [],
        }
        if hasattr(self.repo, "save_scoped_memory"):
            self.repo.save_scoped_memory(f"paper:{paper_id}", paper_memory)
        else:
            self.repo.save_memory(paper_id, paper_memory)
        self.memory_service.initialize_paper_memory_from_overview(paper_id=paper_id, overview=overview)
        self.memory_service.update_user_memory_from_ingestion(
            paper_id=paper_id,
            overview=overview,
        )
        self.repo.update_job(
            job_id,
            {
                "status": "completed",
                "stage": "indexed",
                "progress": 100,
                "updated_at": now,
            },
        )
        logger.info("ingestion.complete: paper_id=%s job_id=%s", paper_id, job_id)

    def get_job(self, job_id: str) -> dict:
        job = self.repo.get_job(job_id)
        if job is None:
            raise KeyError(f"job not found: {job_id}")
        return job

    @staticmethod
    def _merge_formula_citations(
        formulas: list[dict],
        default_citation: dict,
    ) -> list[dict]:
        merged = []
        for index, formula in enumerate(formulas):
            merged.append(
                {
                    "formula_id": formula.get("formula_id", f"formula-generated-{index + 1}"),
                    "latex": formula.get("latex", "S(q, c) = rel(q, c)"),
                    "explanation": formula.get("explanation", "该公式描述了问题与证据匹配关系。"),
                    "variables": formula.get(
                        "variables",
                        [{"symbol": "q", "meaning": "user question"}, {"symbol": "c", "meaning": "candidate chunk"}],
                    ),
                    "citation": formula.get("citation", default_citation),
                }
            )
        return merged or [
            {
                "formula_id": "formula-generated-1",
                "latex": "S(q, c) = rel(q, c)",
                "explanation": "该公式描述了问题与证据匹配关系。",
                "variables": [{"symbol": "q", "meaning": "user question"}, {"symbol": "c", "meaning": "candidate chunk"}],
                "citation": default_citation,
            }
        ]

    @staticmethod
    def _merge_experiment_citations(
        experiments: list[dict],
        default_citation: dict,
    ) -> list[dict]:
        merged = []
        for experiment in experiments:
            merged.append(
                {
                    "claim": experiment.get("claim", "实验部分展示了方法效果。"),
                    "evidence": experiment.get("evidence", "实验用于验证系统关键设计。"),
                    "what_it_proves": experiment.get("what_it_proves", "该实验说明某个模块确实有效。"),
                    "citation": experiment.get("citation", default_citation),
                }
            )
        return merged or [
            {
                "claim": "实验部分展示了方法效果。",
                "evidence": "实验用于验证系统关键设计。",
                "what_it_proves": "该实验说明某个模块确实有效。",
                "citation": default_citation,
            }
        ]
