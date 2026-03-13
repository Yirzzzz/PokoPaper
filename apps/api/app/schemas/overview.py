from pydantic import BaseModel

from app.schemas.common import Citation


class FormulaVariable(BaseModel):
    symbol: str
    meaning: str


class KeyFormula(BaseModel):
    formula_id: str
    latex: str
    explanation: str
    variables: list[FormulaVariable]
    citation: Citation


class ExperimentFinding(BaseModel):
    claim: str
    evidence: str
    what_it_proves: str | None = None
    citation: Citation


class KeyModule(BaseModel):
    name: str
    purpose: str
    why_it_matters: str


class TransferableInsight(BaseModel):
    idea: str
    how_to_apply: str


class RecommendedReading(BaseModel):
    title: str
    reason: str
    relation_to_current_paper: str
    suggested_section: str
    difficulty_level: str


class PrerequisiteTopic(BaseModel):
    topic: str
    reason: str


class PaperOverviewResponse(BaseModel):
    paper_id: str
    tldr: str
    research_motivation: str
    problem_definition: str
    main_contributions: list[str]
    method_summary: str
    key_modules: list[KeyModule]
    key_formulas: list[KeyFormula]
    main_experiments: list[ExperimentFinding]
    limitations: list[str]
    prerequisite_knowledge: list[PrerequisiteTopic]
    conclusion: str
    transferable_insights: list[TransferableInsight]
    recommended_readings: list[RecommendedReading]
