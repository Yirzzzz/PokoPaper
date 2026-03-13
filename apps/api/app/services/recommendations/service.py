class RecommendationService:
    def get_recommendations(self, paper_id: str, category: str | None = None) -> dict:
        items = [
            {
                "type": "prerequisite",
                "title": "Attention Is All You Need",
                "reason": "补齐注意力与编码器基础，便于理解当前论文的检索建模。",
                "relation_to_current_paper": "提供底层建模背景。",
                "suggested_section": "3.2 Scaled Dot-Product Attention",
                "difficulty_level": "beginner",
            },
            {
                "type": "related",
                "title": "REALM",
                "reason": "理解检索增强语言模型如何接入知识检索。",
                "relation_to_current_paper": "同属 retrieval-augmented 范式，但目标不是教学型陪读。",
                "suggested_section": "Method",
                "difficulty_level": "intermediate",
            },
            {
                "type": "contrast",
                "title": "A Simple PDF Chat Baseline",
                "reason": "对比 plain top-k retrieval 与问题类型路由的差异。",
                "relation_to_current_paper": "体现当前系统的增量价值。",
                "suggested_section": "Experiments",
                "difficulty_level": "beginner",
            },
        ]
        if category:
            items = [item for item in items if item["type"] == category]
        return {"paper_id": paper_id, "items": items}
