from app.repositories.factory import get_repository


class PaperService:
    def __init__(self) -> None:
        self.repo = get_repository()

    def list_papers(self) -> list[dict]:
        return self.repo.list_papers()

    def get_paper(self, paper_id: str) -> dict:
        paper = self.repo.get_paper(paper_id)
        if paper is None:
            raise KeyError(f"paper not found: {paper_id}")
        return paper

    def get_structure(self, paper_id: str) -> dict:
        structure = self.repo.get_structure(paper_id)
        if structure is None:
            raise KeyError(f"structure not found: {paper_id}")
        return structure

    def update_paper(self, paper_id: str, category: str | None, tags: list[str] | None) -> dict:
        paper = self.repo.get_paper(paper_id)
        if paper is None:
            raise KeyError(f"paper not found: {paper_id}")
        if category is not None:
            paper["category"] = category
        if tags is not None:
            paper["tags"] = tags
        return self.repo.upsert_paper(paper)

    def delete_paper(self, paper_id: str) -> None:
        self.repo.delete_paper(paper_id)
