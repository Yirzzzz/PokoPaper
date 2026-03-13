from pydantic import BaseModel


class PaperCard(BaseModel):
    id: str
    title: str
    authors: list[str]
    abstract: str
    status: str
    progress_percent: int
    category: str | None = None
    tags: list[str] = []


class UploadPaperResponse(BaseModel):
    paper_id: str
    job_id: str
    status: str


class PaperStructureSection(BaseModel):
    section_title: str
    section_path: str
    page_start: int
    page_end: int


class PaperStructureResponse(BaseModel):
    paper_id: str
    sections: list[PaperStructureSection]
    formulas_count: int
    tables_count: int
    figures_count: int


class UpdatePaperRequest(BaseModel):
    category: str | None = None
    tags: list[str] | None = None
