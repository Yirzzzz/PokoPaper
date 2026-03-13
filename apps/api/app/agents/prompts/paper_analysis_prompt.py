from __future__ import annotations


def build_paper_analysis_prompt(
    title: str,
    abstract: str,
    sections: list[dict],
    chunks: list[dict],
) -> str:
    section_text = "\n".join(
        f"- {section['section_title']} (p.{section['page_start']}-{section['page_end']})"
        for section in sections[:12]
    )
    chunk_text = "\n\n".join(
        f"[{chunk['section_title']} | {chunk['chunk_type']} | p.{chunk['page_num']}]\n{chunk['content'][:800]}"
        for chunk in chunks[:10]
    )
    return f"""
你是一个面向论文初学者的 Paper Companion Agent。你的任务不是泛泛总结，而是把论文拆成“帮助理解”的结构化分析结果。

请严格基于给定论文内容，输出 JSON，不要输出额外解释，不要使用 Markdown 代码块。

论文标题：
{title}

论文摘要：
{abstract}

章节信息：
{section_text}

关键正文片段：
{chunk_text}

请输出以下 JSON 结构：
{{
  "tldr": "一句话总结",
  "research_motivation": "研究动机",
  "problem_definition": "论文要解决的核心问题",
  "main_contributions": ["贡献1", "贡献2"],
  "method_summary": "方法主线",
  "key_modules": [
    {{
      "name": "模块名",
      "purpose": "这个模块是干什么的",
      "why_it_matters": "为什么重要"
    }}
  ],
  "key_formulas": [
    {{
      "formula_id": "formula-1",
      "latex": "如果原文没有明确公式可写占位式",
      "explanation": "公式直观解释",
      "variables": [
        {{"symbol": "x", "meaning": "变量含义"}}
      ]
    }}
  ],
  "main_experiments": [
    {{
      "claim": "实验结论",
      "evidence": "这个实验表明了什么",
      "what_it_proves": "它证明了哪个模块/设计有效"
    }}
  ],
  "limitations": ["局限1", "局限2"],
  "prerequisite_knowledge": [
    {{
      "topic": "建议补充的知识点",
      "reason": "为什么需要先补"
    }}
  ],
  "conclusion": "论文的整体结论",
  "transferable_insights": [
    {{
      "idea": "可迁移的思想",
      "how_to_apply": "能借鉴到什么别的任务或领域"
    }}
  ],
  "recommended_readings": [
    {{
      "title": "推荐阅读标题",
      "reason": "推荐原因",
      "relation_to_current_paper": "与当前论文的关系",
      "suggested_section": "建议优先阅读的部分",
      "difficulty_level": "beginner/intermediate/advanced"
    }}
  ]
}}

要求：
1. 面向初学者，先讲清楚作用，再讲技术细节。
2. 实验部分必须指出“哪个实验验证了哪个模块或设计”。
3. 如果原文信息不足，不要编造，使用谨慎表述。
""".strip()


def build_agent_answer_prompt(
    question: str,
    overview: dict,
    evidence_chunks: list[dict],
    memory: dict,
) -> str:
    evidence_text = "\n\n".join(
        f"[{chunk['section_title']} | p.{chunk['page_num']} | {chunk['chunk_type']}]\n{chunk['content'][:600]}"
        for chunk in evidence_chunks[:4]
    )
    return f"""
你是一个论文陪读智能体。请根据“结构化论文分析 + 证据片段 + 用户阅读记忆”回答用户的当前问题。

用户问题：
{question}

用户阅读记忆：
{memory}

对话长记忆摘要：
{memory.get("conversation_summary", "")}

最近问题：
{memory.get("recent_questions", [])}

结构化论文分析：
{overview}

检索到的证据片段：
{evidence_text}

输出要求：
1. 用中文 Markdown 回答。
2. 第一段必须直接回答用户当前问题，不要先复述整篇论文概览。
3. 回答应围绕当前问题展开，只使用与问题相关的分析结论和证据，不要把整篇论文重新总结一遍。
4. 如果合适，先给直观解释，再给技术解释。
5. 明确区分“论文明确写了”与“根据上下文推断”。
6. 如果用户背景不足，再补充前置知识；不要喧宾夺主。
7. 如果问题问到实验，必须明确回答“这个实验到底证明了什么”。
8. 如果问题问到公式，必须解释公式含义、变量作用、它在方法中的角色。
9. 如果证据不足，请直接说“当前证据不足以确定”，不要编造。
""".strip()
