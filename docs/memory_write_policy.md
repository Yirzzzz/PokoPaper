# Memory Write Policy

## 1. 为什么需要 write policy

当前项目已经有分层记忆：

- conversation memory
- user memory
- paper memory

如果没有独立的 write policy，长期记忆很容易出现几个问题：

- 写入规则散落在业务代码里，难以解释
- 什么该写、什么不该写，没有统一门槛
- user / paper / conversation 三层边界容易混乱
- 长期记忆会被单次情绪化问题或闲聊污染
- 后续做 recall / debug 时，缺少结构化写入证据

所以这次改造的目标不是做“更复杂的 memory”，而是做一个：

- 可解释
- 可扩展
- 可展示
- 对现有系统侵入小

的写入策略层。

---

## 2. 这次改造的核心思路

把“记忆写入”拆成两个职责：

### 2.1 Policy 决策层

负责回答：

- 这一轮有没有值得写入的内容？
- 应该写到哪一层？
- 应该 append / update / merge / ignore？
- 置信度够不够？

对应代码：

- [write_policy.py](/Users/yirz/PyCharmProject/pokomon/apps/api/app/services/memory/write_policy.py)

### 2.2 MemoryService 应用层

负责回答：

- 这条决策如何真正写入存储？
- 如何去重？
- 如何处理冲突？
- 如何记录 meta 信息？

对应代码：

- [service.py](/Users/yirz/PyCharmProject/pokomon/apps/api/app/services/memory/service.py)

这样可以把“规则”和“落库”分开。

---

## 3. 改造前 vs 改造后

### 改造前

写入逻辑主要散在 `MemoryService` 中，特点是：

- 规则以 scattered `if-else` 为主
- user / paper 写入逻辑耦合在一起
- 置信度只有很粗的阈值，没有统一决策结构
- 很难直接展示“这一轮为什么写了这个 memory”
- inspect/debug 不方便

表现出来的问题是：

- 长期记忆容易脏
- 很难向面试官清楚解释“memory write policy”
- 后续要接 recall / RAG 时，可扩展性一般

### 改造后

现在引入了独立 write policy，特点是：

- 所有写入先产出结构化 `MemoryWriteDecision`
- 每条候选写入都带有：
  - target_scope
  - target_field
  - operation
  - reason
  - confidence
  - evidence_count
  - source_type
  - last_updated_at
- 低于阈值的候选自动变成 `ignore`
- `MemoryService` 只做 apply / dedup / conflict resolution / meta persistence
- 可以直接 inspect 输入对话，输出结构化决策

这更像一个“agent 在思考如何写 memory”的系统，而不只是若干业务分支。

---

## 4. 当前策略支持哪些字段

### 4.1 user memory

当前优先支持：

- `weak_concepts`
- `mastered_concepts`
- `preferred_explanation_style`
- `recent_topics`
- `cross_paper_links`

### 4.2 paper memory

当前优先支持：

- `motivation`
- `method`
- `key_results`
- `keywords`

### 4.3 conversation memory

当前优先支持：

- `active_topics`
- `conversation_summary`

这两个字段保存在 `session:{conversation_id}` 作用域中，作为 conversation 级结构化补充。

---

## 5. 写入决策结构

核心结构定义在：

- [memory.py](/Users/yirz/PyCharmProject/pokomon/apps/api/app/schemas/memory.py)

### 5.1 MemoryWriteDecision

```python
MemoryWriteDecision:
  should_write
  reason
  threshold
  writes
```

### 5.2 MemoryWriteAction

```python
MemoryWriteAction:
  target_scope
  target_field
  operation
  value
  reason
  confidence
  evidence_count
  source_type
  last_updated_at
```

这套结构的目标是：

- 让每次写入都有解释
- 让每次 ignore 也有解释
- 让后续 recall / debug 有稳定输入

---

## 6. 当前规则设计

### 6.1 weak_concepts

规则：

- 需要出现明确困惑信号，例如：
  - `没懂`
  - `不理解`
  - `困惑`
- 概念必须可识别
- 如果同概念历史上已经进入 `weak_concepts`，会加一点置信度

设计理由：

- 防止“用户偶然问一句”就污染长期记忆
- 让 repeated confusion 比 single noise 更可信

### 6.2 mastered_concepts

规则：

- 需要明确 mastery 信号，例如：
  - `我懂了`
  - `我明白了`
  - `掌握了`

冲突处理：

- 如果某概念进入 `mastered_concepts`
- 会从 `weak_concepts` 中移除

### 6.3 preferred_explanation_style

规则：

- 只有明确、稳定的风格偏好才写，例如：
  - `以后都先讲直觉再讲公式`
  - `之后默认多举例`

像这种：

- `能通俗举例吗？`

只会生成低置信候选，并被阈值自动标成 `ignore`。

设计理由：

- 一次性表达不应直接污染长期偏好
- 长期偏好必须来自更稳定的指令

### 6.4 recent_topics

来源分两类：

#### 上传 / overview

- 置信度更高
- 因为它代表“最近读了什么”

#### dialog

- 置信度更低
- 更像即时讨论主题

### 6.5 paper memory

paper memory 只接收与当前论文强相关的信息：

- `motivation`
- `method`
- `key_results`
- `keywords`

并且：

- upload / overview 写入置信度高于普通 dialog 推断
- dialog 只有在当前问题明显围绕该 paper 的方法/实验/动机时才会触发

---

## 7. 轻量置信度机制

这次没有引入复杂模型评分，而是做了一个可解释的轻量版。

核心原则：

- 显式表达 > 推断表达
- 多轮重复 > 单轮偶发
- upload / overview > dialog
- 带直接证据 > 弱推断

例如：

- `以后都先讲直觉再讲公式`
  - 高置信，可写入 `preferred_explanation_style`

- `能通俗举例吗`
  - 低置信，默认 `ignore`

- overview 中的 `method_summary`
  - 高置信，可直接更新 `paper.method`

---

## 8. 写入阈值

当前统一阈值在：

- [write_policy.py](/Users/yirz/PyCharmProject/pokomon/apps/api/app/services/memory/write_policy.py)

```python
WRITE_CONFIDENCE_THRESHOLD = 0.68
```

规则：

- `confidence >= threshold`
  - 才允许真实写入
- `confidence < threshold`
  - 自动改成 `operation = ignore`

这个设计的价值是：

- 把“写不写”的门槛显式化
- 防止长期记忆被低价值候选污染
- inspect 时仍然能看到候选是如何被拒绝的

---

## 9. 冲突处理与更新策略

当前支持最小但足够清晰的冲突规则：

### 9.1 list 字段

例如：

- `weak_concepts`
- `mastered_concepts`
- `recent_topics`
- `keywords`
- `active_topics`

使用：

- `append`
- `merge`
- 去重

### 9.2 scalar 字段

例如：

- `preferred_explanation_style`
- `motivation`
- `method`
- `key_results`
- `conversation_summary`

使用：

- `update`

覆盖规则：

- 新值置信度高于旧值时，允许覆盖
- 旧值为空时，允许直接写入

### 9.3 weak/mastered 冲突

规则：

- `mastered_concepts` 写入成功后，移除同概念的 `weak_concepts`
- 如果某概念已在 `mastered_concepts` 中，低置信 weak 写入会被拒绝

---

## 10. meta 信息是怎么保存的

为了后续 recall / debug，每次真正写入后会记录最小元信息，包括：

- `target_scope`
- `target_field`
- `operation`
- `write_reason`
- `write_confidence`
- `evidence_count`
- `source_type`
- `source_question`
- `source_answer_preview`
- `updated_at`

这些 meta 保存在现有的：

- `memory_item_meta`

中，没有额外引入重量级存储结构。

---

## 11. debug / inspect 能力

为了演示和调试，这次新增了 inspect 接口：

- `POST /api/v1/memory/write-policy/inspect`

对应代码：

- [memory.py](/Users/yirz/PyCharmProject/pokomon/apps/api/app/api/v1/memory.py)

请求示例：

```json
{
  "source_type": "dialog",
  "session_id": "session-demo",
  "paper_id": "paper-123",
  "question": "我没懂 Retrieval 方法，能解释一下这篇论文的方法吗？",
  "answer": "当然可以，我先讲方法主线。"
}
```

返回示例：

```json
{
  "decision": {
    "should_write": true,
    "reason": null,
    "threshold": 0.68,
    "writes": [
      {
        "target_scope": "conversation",
        "target_field": "active_topics",
        "operation": "merge",
        "confidence": 0.74,
        "reason": "当前问题中出现了可复用的讨论主题..."
      },
      {
        "target_scope": "user",
        "target_field": "weak_concepts",
        "operation": "append",
        "confidence": 0.74,
        "reason": "用户明确表达了困惑..."
      },
      {
        "target_scope": "paper",
        "target_field": "method",
        "operation": "update",
        "confidence": 0.76,
        "reason": "当前问题和论文方法强相关..."
      }
    ]
  }
}
```

这个接口非常适合：

- demo
- 面试展示
- 调策略

---

## 12. 主链路怎么接入 policy

### 12.1 dialog 侧

agent 回答完成后：

- `PaperCompanionAgent`
  - 调用 `process_dialog_memory_writes(...)`

它会：

1. 调 `decide_memory_writes(...)`
2. 产出结构化 decision
3. 再由 `MemoryService.apply_write_decision(...)` 真正落库

### 12.2 ingestion 侧

论文解析完成后：

- ingestion service
  - 调用 `process_ingestion_memory_writes(...)`

它会把 overview 中高置信的 paper / user 信息写入对应 memory。

---

## 13. 为什么这个方案适合面试展示

这套方案适合面试展示，主要因为它兼顾了三点：

### 13.1 有设计感

不是简单“if 命中了就直接存”，而是：

- 先 decision
- 再 apply
- 有 threshold
- 有 confidence
- 有 conflict resolution

### 13.2 有工程感

没有引入重量级基础设施：

- 不改数据库
- 不引入复杂依赖
- 复用现有 store 和 meta 表达

但同时又把策略做成了独立模块，结构清晰。

### 13.3 有扩展感

后续很容易扩展到：

- 更复杂的长期 recall
- RAG 前的 memory candidate ranking
- 用户偏好随时间衰减
- recall explainability

---

## 14. 后续如何扩展到长期 recall / RAG

当前 write policy 已经把关键信息结构化了，后续可以自然扩展：

1. 把高置信 memory item 作为 recall 候选源
2. 按 `target_scope / target_field / confidence / updated_at` 做排序
3. 在 RAG 前先召回 memory candidates
4. 再和 chunk evidence 一起进 prompt

也就是说，这次改造先解决的是：

- memory 写得干净
- 写得可解释
- 写得可调试

而不是一开始就把 recall 和 retrieval 全部做复杂。

---

## 15. 一句话总结

这次的 memory write policy 改造，把原来 scattered 的写入规则收敛成了一套：

- 分层记忆
- 结构化决策
- 轻量置信度
- 阈值过滤
- 冲突处理
- inspect 可演示

的轻量策略系统，既能支持当前项目继续迭代，也足够作为面试展示亮点。
