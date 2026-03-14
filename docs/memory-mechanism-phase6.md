# Pokomon Memory 机制说明（Phase 6）

这份文档描述的是 **当前仓库里已经实现** 的 memory 系统机制，不写未来规划，不把未完成能力写成已完成。

适用范围：
- 本地单用户
- 默认用户固定为 `local-user`
- 主要面向论文阅读、追问、跨论文回忆

---

## 1. 当前 memory 系统解决什么问题

当前 memory 系统主要解决 5 类问题：

1. 页面刷新或服务重启后，聊天历史还能恢复。
2. 同一篇论文内，系统能记住方法、实验、概念、卡点等阅读状态。
3. `/chat` 独立对战记录和论文页问答可以相对独立。
4. 当前问题可以按需从 `session / paper / user` 三层 memory 中召回相关内容。
5. 跨论文问题可以主动回忆“之前读过哪篇相关论文”。

它当前不是：
- embedding memory
- vector memory
- 多用户 memory platform
- 通用 Agent 事件库

更准确地说，它是一个：

- `session-scoped memory`
- `paper-scoped reading memory`
- `local-user memory`
- `retrieval-based prompt memory`

---

## 2. 三层 scope

当前 memory scope 已固定为三层：

- `session:{session_id}`
- `paper:{paper_id}`
- `user:local-user`

### 2.1 session scope

作用：
- 支持短期连续追问
- 支持页面刷新后恢复当前会话上下文

当前字段：
- `recent_questions`
- `conversation_summary`
- `recent_turn_summaries`
- `active_topics`
- `updated_at`

特点：
- 属于短期上下文
- 不应该默认上升为长期知识记忆

### 2.2 paper scope

作用：
- 保存某篇论文的稳定阅读记忆
- 和具体某次 session 解耦

当前字段：
- `progress_status`
- `progress_percent`
- `last_read_section`
- `stuck_points`
- `key_questions`
- `important_takeaways`
- `method_summary`
- `experiment_takeaways`
- `concepts_seen`
- `linked_papers`

特点：
- 既包含 UI/阅读状态字段
- 也包含更接近 agent memory 的结构化字段

### 2.3 user scope

作用：
- 保存本地单用户的全局阅读痕迹
- 支持跨论文 recall

当前字段：
- `read_paper_ids`
- `preferred_explanation_style`
- `recent_topics`
- `weak_concepts`
- `mastered_concepts`
- `cross_paper_links`

当前固定用户：

```python
DEFAULT_USER_ID = "local-user"
```

---

## 3. 数据存储位置

默认存储是本地 JSON：

- `storage/db/store.json`

相关仓储：
- [apps/api/app/repositories/local_store.py](/Users/yirz/PyCharmProject/pokomon/apps/api/app/repositories/local_store.py)
- [apps/api/app/repositories/postgres_store.py](/Users/yirz/PyCharmProject/pokomon/apps/api/app/repositories/postgres_store.py)

当前和 memory 直接相关的顶层键：
- `memories`
- `chat_sessions`
- `chat_messages`
- `memory_item_states`
- `memory_item_meta`

其中：
- `memories` 保存三层 scoped memory
- `chat_messages` 保存原始消息历史
- `memory_item_states` 保存 item 是否启用
- `memory_item_meta` 保存 write reason / source question / answer preview 等元数据

---

## 4. 原始聊天消息 vs summary memory vs 长期 memory

当前实现里，这三者已经明确分开。

### 4.1 原始聊天消息

保存位置：
- `chat_messages`

写入时机：
- 用户发问就写 user message
- 生成回答后写 assistant message

特点：
- 永远保留
- 不受 summary gate 影响
- 这是聊天恢复的基础

关键代码：
- [apps/api/app/api/v1/chat.py](/Users/yirz/PyCharmProject/pokomon/apps/api/app/api/v1/chat.py)

### 4.2 session summary memory

保存位置：
- `session:{session_id}`

作用：
- 给当前会话提供压缩后的短期上下文

特点：
- 不是每轮都更新
- 只有“高价值轮次”才会进入

当前会被 summary gate 拦下的低价值轮次：
- `你好`
- `谢谢`
- `继续`
- `展开一点`
- 以及其他 `low_signal_turn / memory_not_needed`

也就是说：
- 原始消息会保存
- 但 `conversation_summary / recent_turn_summaries / recent_questions` 不会被这类轮次污染

关键代码：
- [apps/api/app/services/memory/service.py](/Users/yirz/PyCharmProject/pokomon/apps/api/app/services/memory/service.py)
  - `should_update_summary_memory(...)`
  - `update_session_memory(...)`

### 4.3 结构化长期 memory

保存位置：
- `paper:{paper_id}`
- `user:local-user`

作用：
- 保存稳定的论文理解、概念薄弱点、跨论文关系等

这部分不是无脑写入，而是要先经过 write pipeline。

---

## 5. Phase 3：memory write pipeline

当前长期 memory 写入采用的是：

- `gate -> extract -> apply`

### 5.1 gate

先判断这一轮是否值得进入长期 memory。

低价值轮次直接跳过，例如：
- `你好`
- `谢谢`
- `继续`
- `展开一点`

### 5.2 extract

如果通过 gate，就生成结构化写入动作：

- `MemoryWriteDecision`
- `MemoryWriteAction`

核心字段：

```python
MemoryWriteDecision:
  should_write
  reason
  writes

MemoryWriteAction:
  target_scope
  memory_type
  payload
  confidence
```

### 5.3 apply

把结构化 action 应用到：
- `paper:{paper_id}`
- `user:local-user`

支持的典型 memory type：

paper:
- `stuck_point`
- `important_takeaway`
- `method_summary`
- `experiment_takeaway`
- `concept_seen`
- `linked_paper`

user:
- `weak_concept`
- `mastered_concept`
- `cross_paper_link`
- `topic_interest`
- `explanation_preference`

### 5.4 去重和置信度

当前已有最小去重控制：
- 相同 concept 不重复堆
- 相同 linked paper 不重复堆
- 相同 cross paper link 不重复堆

同时有置信度门槛：
- 低于阈值的 action 不落库

---

## 6. Phase 4：memory retrieval baseline

当前系统已经不是“默认把所有 memory 塞进 prompt”。

而是先做 retrieval：

- `route -> retrieve -> rank/select -> inject`

### 6.1 route

当前支持这些 route：

- `paper_understanding`
- `concept_support`
- `cross_paper_recall`
- `session_followup`
- `low_signal_turn`
- `memory_not_needed`

### 6.2 retrieve

候选来源：

session:
- `recent_turn_summaries`
- `active_topics`

paper:
- `stuck_points`
- `important_takeaways`
- `method_summary`
- `experiment_takeaways`
- `concepts_seen`
- `linked_papers`

user:
- `weak_concepts`
- `mastered_concepts`
- `recent_topics`
- `cross_paper_links`

### 6.3 score

当前是规则 + 轻量关键词重叠，不是 embedding。

打分依据：
- route 与 memory_type 是否匹配
- scope 是否匹配
- 关键词 / 概念词是否重叠
- 当前 paper 是否匹配

### 6.4 top-k

当前注入预算：
- session: 2
- paper: 3
- user: 2

### 6.5 retrieval 输出结构

```python
MemoryRetrievalResult:
  should_retrieve
  reason
  route
  items

RetrievedMemoryItem:
  source_scope
  memory_type
  payload
  score
```

---

## 7. Phase 5：cross-paper proactive recall

在跨论文问题上，当前系统已经能主动做 recall。

典型问题：
- 我之前看过哪篇也用了这个方法？
- 这个概念我是不是在哪篇论文里见过？
- 这篇和之前那篇有什么区别？
- 有没有论文和这篇技术路线很像？

### 7.1 recall 候选来源

优先复用已有 memory，不另起系统。

当前使用：

paper scope:
- `linked_papers`
- `concepts_seen`
- `method_summary`
- `important_takeaways`

user scope:
- `read_paper_ids`
- `weak_concepts`
- `recent_topics`
- `mastered_concepts`
- `cross_paper_links`

### 7.2 recall 输出结构

```python
CrossPaperRecallResult:
  should_recall
  reason
  candidates

RecalledPaperCandidate:
  paper_id
  title
  relation_reason
  supporting_memory_ids
  score
```

### 7.3 recall 的作用

它不会替代当前论文证据，只是补充上下文：
- 候选论文是谁
- 为什么相关
- 相关点在哪里

---

## 8. Phase 6：retrieval-based memory 正式接管 prompt 注入

这是当前版本里最重要的一步。

现在 memory 注入优先级已经是：

1. `retrieved memory`
   - `session_memory`
   - `paper_memory`
   - `user_memory`

2. `cross_paper_recall`
   - 只在需要时注入

3. `fallback_summary`
   - `conversation_summary`
   - 极少量 `recent_questions`

也就是说：
- `conversation_summary` 不再是默认主 memory 来源
- `recent_questions` 也不再是默认主输入

### 8.1 当前 prompt memory 结构

`build_prompt_memory(...)` 现在会输出结构化块：

- `session_memory`
- `paper_memory`
- `user_memory`
- `cross_paper_recall`
- `fallback_summary`

并附带：

- `memory_retrieval`
  - `route`
  - `injected_count`
  - `fallback_to_summary`
  - `fallback_reason`

### 8.2 fallback 触发条件

当前典型 fallback reason：
- `no_retrieved_memory`
- `missing_session_followup_memory`

只有在 retrieval 命中不足时，才会带：
- `conversation_summary`
- 最近 2 条 `recent_questions`

### 8.3 current budgets

- session memory items: 2
- paper memory items: 3
- user memory items: 2
- cross-paper recall candidates: 3
- fallback recent questions: 2
- fallback summary: 截断到较短长度

---

## 9. Memory Lab 是怎么组织出来的

当前仓库里已经有一个独立的 `Memory Lab` 页面。

路径：
- `/memory-lab`

作用：
- 查看三层 memory
- 按 scope/type/paper/enabled 过滤
- 查看单条 memory 详情
- enable / disable / delete
- reset 一批 memory

### 9.1 它不是独立事件库

当前 Memory Lab 不是基于独立 event sourcing 系统，而是：

- 基于现有 `scoped memory`
- 在 `MemoryService` 中做 item projection

也就是说，它是一个：
- `memory item view layer`

### 9.2 memory item 包含什么

当前 item 字段：
- `memory_id`
- `scope`
- `scope_type`
- `scope_id`
- `memory_type`
- `payload`
- `summary`
- `paper_id`
- `paper_title`
- `created_at`
- `updated_at`
- `is_enabled`
- `write_reason`
- `write_confidence`
- `source_question`
- `source_answer_preview`

### 9.3 旧 memory 的限制

旧 memory 可能没有：
- `write_reason`
- `source_question`
- `source_answer_preview`

这是允许的，当前页面会兼容空值。

---

## 10. 新写入 memory 的元数据

从当前实现开始，新写入的长期 memory 会尽量补这些元数据：

- `write_reason`
- `write_confidence`
- `source_question`
- `source_answer_preview`

保存位置：
- `memory_item_meta`

注意：
- 这是针对新写入 item 的增强
- 不是回填旧数据

---

## 11. 低信息量轮次现在如何处理

这是当前实现里一个重要修正点。

例如用户输入：
- `你好`
- `谢谢`
- `继续`
- `展开一点`

现在行为是：

1. 原始 `chat_messages` 仍然保存
2. `conversation_summary` 不更新
3. `recent_turn_summaries` 不更新
4. `recent_questions` 不更新
5. `paper memory` 不写
6. `user memory` 不写

这样做的目的是：
- 不丢真实聊天记录
- 但不让低信息量轮次污染 memory

---

## 12. 当前日志与可观测性

当前后端已经有几类关键日志：

### 12.1 write logs

- `memory.write decision`
- `memory.write apply`
- `memory.write dedup`

### 12.2 retrieval logs

- `memory.retrieve skipped`
- `memory.retrieve result`

### 12.3 recall logs

- `memory.recall skipped`
- `memory.recall result`

### 12.4 injection logs

- `memory.inject`

会记录：
- route
- 各 block 注入多少条
- recall candidate 数量
- 是否 fallback 到 summary
- fallback reason

### 12.5 summary logs

- `memory.summary skipped`

用来说明：
- 哪些轮次被明确排除在 summary 更新之外

---

## 13. 目前没有做的事情

当前还没有做：

- embedding-based memory retrieval
- vector database memory recall
- 多用户体系
- 复杂 memory event graph
- UI 化 recall trace
- 对所有旧 memory 的历史元数据回填

所以当前系统最准确的描述是：

> 一个本地单用户、三层 scope、结构化写入、规则检索、支持跨论文主动回忆的论文阅读 memory system。

---

## 14. 面试时如何实事求是地描述

可以直接这样说：

> 这个项目里的 memory 不是一开始就做向量记忆，而是先做了三层 scope：session、paper、user。先把结构化写入和 retrieval baseline 跑通，再把 cross-paper recall 接进回答链路。现在 prompt 注入已经是 retrieval-based memory 为主，conversation summary 只保留为 fallback。

不要说成：
- “我已经做了完整的 long-term memory vector retrieval”
- “memory 已经完全 agentic”
- “我做了多用户长期记忆系统”

这些都不符合当前实现。

---

## 15. 关键代码入口

最关键的实现集中在这里：

- [apps/api/app/services/memory/service.py](/Users/yirz/PyCharmProject/pokomon/apps/api/app/services/memory/service.py)
- [apps/api/app/schemas/memory.py](/Users/yirz/PyCharmProject/pokomon/apps/api/app/schemas/memory.py)
- [apps/api/app/agents/paper_companion_agent.py](/Users/yirz/PyCharmProject/pokomon/apps/api/app/agents/paper_companion_agent.py)
- [apps/api/app/agents/prompts/paper_analysis_prompt.py](/Users/yirz/PyCharmProject/pokomon/apps/api/app/agents/prompts/paper_analysis_prompt.py)
- [apps/api/app/api/v1/memory.py](/Users/yirz/PyCharmProject/pokomon/apps/api/app/api/v1/memory.py)
- [apps/api/app/repositories/local_store.py](/Users/yirz/PyCharmProject/pokomon/apps/api/app/repositories/local_store.py)
- [apps/web/app/(dashboard)/memory-lab/page.tsx](/Users/yirz/PyCharmProject/pokomon/apps/web/app/(dashboard)/memory-lab/page.tsx)
- [apps/web/components/memory/memory-lab.tsx](/Users/yirz/PyCharmProject/pokomon/apps/web/components/memory/memory-lab.tsx)

---

## 16. 当前测试覆盖

当前后端测试已经覆盖：

- legacy memory 迁移
- 三层 scope 分离
- 结构化字段写入
- low-signal turn 不进入长期 memory
- retrieval routing
- cross-paper recall
- prompt memory fallback
- Memory Lab item 管理
- low-signal turn 不污染 summary

测试文件：
- [apps/api/tests/test_memory_scope.py](/Users/yirz/PyCharmProject/pokomon/apps/api/tests/test_memory_scope.py)

