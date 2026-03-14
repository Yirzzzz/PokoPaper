# Pokomon 记忆系统实现说明

这份文档只描述 **当前项目里已经实现的记忆系统**，不写未来规划，不把未完成能力写成已实现。

---

## 1. 当前记忆系统的定位

当前项目的记忆系统不是通用 Agent 的全局长期记忆，而是一个 **论文阅读场景下的持久化上下文系统**。

它主要解决 3 个问题：

1. 用户刷新页面或重启服务后，对话历史不要丢。
2. 同一篇论文里，系统要记住最近问过什么、回答过什么。
3. `/chat` 对战记录页和论文详情页的问答，要能相对独立，而不是强行共用一套对话历史。

所以它现在更准确的名字应该是：

- `paper-level memory`
- `session-scoped memory`
- `reading episode memory`

而不是完整的跨论文 semantic memory。

---

## 2. 记忆系统目前包含哪些层

当前实现里，记忆主要分两层：

### 2.1 聊天历史层

这层负责保存原始对话消息。

保存内容：

- `session_id`
- `message_id`
- `role`
- `content_md`
- `citations`
- `created_at`

作用：

- 页面刷新后重新拉历史消息
- 服务重启后仍可恢复对话

关键代码：

- [apps/api/app/api/v1/chat.py](/Users/yirz/PyCharmProject/pokomon/apps/api/app/api/v1/chat.py)
- [apps/api/app/repositories/local_store.py](/Users/yirz/PyCharmProject/pokomon/apps/api/app/repositories/local_store.py)
- [apps/web/components/chat/chat-panel.tsx](/Users/yirz/PyCharmProject/pokomon/apps/web/components/chat/chat-panel.tsx)

---

### 2.2 对话摘要记忆层

这层负责把历史问答压缩成可以继续注入 prompt 的摘要信息。

当前保存内容：

- `conversation_summary`
- `recent_questions`
- `key_questions`
- `progress_status`
- `progress_percent`
- `last_read_section`
- `stuck_points`

作用：

- 下一轮问答前，给模型一个“最近聊过什么”的短摘要
- 让系统知道这篇论文读到哪里
- 让系统知道最近卡在哪里

关键代码：

- [apps/api/app/services/memory/service.py](/Users/yirz/PyCharmProject/pokomon/apps/api/app/services/memory/service.py)
- [apps/api/app/agents/paper_companion_agent.py](/Users/yirz/PyCharmProject/pokomon/apps/api/app/agents/paper_companion_agent.py)

---

## 3. 记忆数据存在哪里

### 3.1 当前默认存储

当前默认是本地 JSON 存储。

存储文件：

- `storage/db/store.json`

仓储实现：

- [apps/api/app/repositories/local_store.py](/Users/yirz/PyCharmProject/pokomon/apps/api/app/repositories/local_store.py)

这个文件里当前会保存：

- `papers`
- `jobs`
- `structures`
- `overviews`
- `memories`
- `chat_sessions`
- `chat_messages`

其中和记忆直接相关的是：

- `memories`
- `chat_sessions`
- `chat_messages`

---

### 3.2 PostgreSQL 适配层

项目里也有 PostgreSQL 仓储适配层，但当前主工作流还是本地 JSON 为主。

相关代码：

- [apps/api/app/repositories/postgres_store.py](/Users/yirz/PyCharmProject/pokomon/apps/api/app/repositories/postgres_store.py)

这里已经实现了：

- `create_chat_session`
- `create_chat_message`
- `list_chat_messages`
- `save_memory`
- `get_memory`

但现在最稳定、最常用的还是本地 JSON。

---

## 4. 聊天历史是怎么持久化的

### 4.1 session 的创建

当用户进入问答页时，前端会先请求会话。

论文详情页问答：

- 调用 `GET /api/v1/chat/sessions/by-paper/{paper_id}`

独立 `/chat` 对战记录页：

- 调用 `GET /api/v1/chat/sessions/by-key/{session_key}?paper_id=...`

这里的区别是：

- 论文详情页：按 `paper_id` 复用固定 session
- `/chat` 页：按 `session_key` 建独立 session

关键代码：

- [apps/api/app/api/v1/chat.py](/Users/yirz/PyCharmProject/pokomon/apps/api/app/api/v1/chat.py)

示意代码：

```python
@router.get("/sessions/by-paper/{paper_id}")
def get_or_create_chat_session_for_paper(paper_id: str) -> dict:
    existing = repo.get_chat_session_by_paper(paper_id)
    if existing is not None:
        return existing
```

```python
@router.get("/sessions/by-key/{session_key}")
def get_or_create_chat_session_by_key(session_key: str, paper_id: str) -> dict:
    existing = repo.get_chat_session_by_key(session_key)
    if existing is not None:
        return existing
```

---

### 4.2 消息的保存

每次问答时，后端会：

1. 先保存用户消息
2. 再调用 Agent 生成回答
3. 再保存 assistant 消息

关键代码：

- [apps/api/app/api/v1/chat.py](/Users/yirz/PyCharmProject/pokomon/apps/api/app/api/v1/chat.py)

示意代码：

```python
repo.create_chat_message(
    {
        "message_id": f"message-user-{uuid4().hex[:8]}",
        "session_id": session_id,
        "role": "user",
        "content_md": payload.question,
        "citations": [],
        "created_at": datetime.now(UTC).isoformat(),
    }
)
```

```python
repo.create_chat_message(
    {
        "message_id": answer["message_id"],
        "session_id": session_id,
        "role": "assistant",
        "content_md": answer["answer_md"],
        "citations": answer["citations"],
        "created_at": datetime.now(UTC).isoformat(),
    }
)
```

---

### 4.3 前端如何恢复历史

前端 `ChatPanel` 在挂载时会：

1. 获取当前 session
2. 请求该 session 的消息列表
3. 把结果 hydrate 到 Zustand

关键代码：

- [apps/web/components/chat/chat-panel.tsx](/Users/yirz/PyCharmProject/pokomon/apps/web/components/chat/chat-panel.tsx)
- [apps/web/store/app-store.ts](/Users/yirz/PyCharmProject/pokomon/apps/web/store/app-store.ts)

核心逻辑：

```tsx
const messages = await fetchChatMessages(session.session_id);
hydrateChatHistory(chatStateKey, messages);
```

所以：

- 页面刷新不会丢
- 只要 session 一样，历史就能恢复

---

## 5. 对话摘要记忆是怎么实现的

这部分是当前“长记忆”的核心。

### 5.1 保存的数据结构

在 `MemoryService` 中，如果某篇论文还没有记忆，会返回这个基础结构：

```python
{
    "paper_id": paper_id,
    "progress_status": "new",
    "progress_percent": 0,
    "last_read_section": "Introduction",
    "stuck_points": [],
    "key_questions": [],
    "conversation_summary": "",
    "recent_questions": [],
}
```

关键代码：

- [apps/api/app/services/memory/service.py](/Users/yirz/PyCharmProject/pokomon/apps/api/app/services/memory/service.py)

---

### 5.2 每轮问答后如何更新

每次回答完成后，Agent 会调用：

```python
self.memory_service.update_conversation_memory(
    paper_id=paper_id,
    question=question,
    answer=answer["answer_md"],
    memory_key=memory_key,
)
```

这个方法会做几件事：

1. 把当前问题追加进 `recent_questions`
2. 把当前问题和回答摘要追加到 `conversation_summary`
3. 如果问题没出现过，则加入 `key_questions`
4. 对长度做裁剪，防止无限增长

实现代码：

```python
recent_questions = [*memory.get("recent_questions", []), question][-8:]
answer_preview = " ".join(answer.split())[:240]

if prior_summary:
    summary = f"{prior_summary}\n- Q: {question}\n- A: {answer_preview}"
else:
    summary = f"- Q: {question}\n- A: {answer_preview}"

memory["conversation_summary"] = summary[-4000:]
memory["recent_questions"] = recent_questions
```

关键文件：

- [apps/api/app/services/memory/service.py](/Users/yirz/PyCharmProject/pokomon/apps/api/app/services/memory/service.py)

这说明当前的“长记忆”并不是重新总结整段对话，而是：

- 保留最近问题列表
- 保留问答摘要串
- 在下一轮继续喂给模型

---

## 6. 这些记忆是如何参与回答的

当前记忆进入回答链路的方式是：

1. `PaperCompanionAgent.answer()` 先取 memory
2. 再调用 `RAGService.answer_question()`
3. 把 memory 一起传进去

关键代码：

- [apps/api/app/agents/paper_companion_agent.py](/Users/yirz/PyCharmProject/pokomon/apps/api/app/agents/paper_companion_agent.py)

```python
memory = self.memory_service.get_paper_memory(
    paper_id=paper_id,
    memory_key=memory_key,
)

answer = self.rag_service.answer_question(
    paper_id=paper_id,
    question=question,
    selected_model=selected_model,
    memory=memory,
    enable_thinking=enable_thinking,
)
```

然后 `RAGService` 会把它传给 `LLMService.generate_grounded_answer()`，再进入 prompt 构造。

关键文件：

- [apps/api/app/services/rag/service.py](/Users/yirz/PyCharmProject/pokomon/apps/api/app/services/rag/service.py)
- [apps/api/app/services/llm/service.py](/Users/yirz/PyCharmProject/pokomon/apps/api/app/services/llm/service.py)

也就是说，当前记忆不是一个独立推理模块，而是：

**作为 prompt 上下文的一部分进入 LLM。**

---

## 7. `/chat` 和论文内问答为什么现在是相对独立的

这是最近做过的一次关键调整。

### 7.1 之前的问题

之前虽然 `/chat` 页和论文详情页 session 已经分开，但二者仍然默认共用 `paper_id` 对应的那份 memory。

结果是：

- session 分开了
- memory 还是混的

这不符合“对战记录和论文页问答相对独立”的目标。

---

### 7.2 现在的实现

现在引入了 `memory_key` 的概念：

- 论文详情页问答：
  - `memory_key = paper_id`
- `/chat` 对战记录页：
  - `memory_key = chat-session:{session_id}`

这样一来：

- 两边仍然共享同一篇论文知识上下文
- 但不会再默认共享同一份对话摘要记忆

关键代码：

- [apps/api/app/api/v1/chat.py](/Users/yirz/PyCharmProject/pokomon/apps/api/app/api/v1/chat.py)
- [apps/api/app/services/memory/service.py](/Users/yirz/PyCharmProject/pokomon/apps/api/app/services/memory/service.py)

核心逻辑：

```python
session = repo.get_chat_session(session_id)
memory_key = payload.paper_id

if session is not None:
    session_key = session.get("session_key") or ""
    if isinstance(session_key, str) and session_key.startswith("chat-hub:"):
        memory_key = f"chat-session:{session_id}"
```

然后把这个 `memory_key` 传给：

- `get_paper_memory(...)`
- `update_conversation_memory(...)`

这就是当前“相对独立”的核心实现方法。

---

## 8. 前端本地状态是怎么配合的

前端除了后端持久化外，还有一层 Zustand 状态，用于当前页面即时交互。

存储内容：

- `sessionId`
- `draftQuestion`
- `selectedModel`
- `enableThinking`
- `turns`
- `historyLoaded`
- `historyMessages`

关键文件：

- [apps/web/store/app-store.ts](/Users/yirz/PyCharmProject/pokomon/apps/web/store/app-store.ts)

这里的作用不是做长期记忆，而是：

- 提高当前页交互流畅度
- 在还没重新请求后端前，先把刚发出的消息显示出来

真正的持久化来源还是后端 `chat_messages + memories`。

---

## 9. 当前实现的优点

### 已解决的问题

- 刷新页面不丢历史
- 服务重启不丢历史
- 同一篇论文可以保持自己的问答上下文
- `/chat` 对战记录可以拥有相对独立的会话和对话记忆
- 问答前可以把近期历史摘要注入 prompt

---

## 10. 当前实现的边界

这部分很重要，面试或后续迭代时要讲清楚。

### 当前还没有做到

#### 1. 没有跨论文的统一 semantic memory

当前 memory 是：

- `paper-level`
- `session-scoped`

不是：

- 全局用户知识图谱
- 概念向量记忆
- 跨论文自动关联回忆

#### 2. 没有真正的摘要压缩模型

当前的 `conversation_summary` 是追加式文本摘要，不是用专门 summarize chain 做分层记忆压缩。

#### 3. 没有“需要时主动回忆其他论文”

用户现在说：

> 回想我在哪篇论文里问过这个概念

系统还不能自动跨 session 检索这类信息。

当前只是把 `/chat` 和论文详情页做成了相对独立，不是全局记忆检索系统。

---

## 11. 可以如何继续演进

如果后续要升级，这个记忆系统最自然的演进路线是：

### 第一步：把 memory 从 paper_id 扩展成真正的 scoped memory

例如：

- `paper:{paper_id}`
- `chat:{session_id}`
- `user:{user_id}`

### 第二步：增加全局 semantic memory

例如：

- 用户经常问哪些概念
- 哪些概念已经掌握
- 偏好什么解释风格
- 近期主要关注哪些研究方向

### 第三步：增加“按需回忆”

即：

- 默认不混用论文页和 `/chat` 的对话
- 但当用户显式问“我之前在哪篇论文里问过这个”时
- 再去跨 session 检索 memory

---

## 12. 结论

当前项目里的记忆系统，可以用一句话总结：

> 它实现的是“论文阅读场景下的持久化对话记忆”，核心做法是把聊天历史和 conversation summary 分别存储，并按 `paper_id / session_id / memory_key` 控制作用范围。

这套实现已经能支持：

- 论文级连续追问
- `/chat` 独立长对话
- 刷新和重启后的历史恢复

但它还不是一个完整的跨论文长期记忆 Agent。

如果你要面试时讲，最稳的说法就是：

> 我先把持久化对话记忆和作用域隔离做对，再逐步演进到全局 semantic memory，而不是一开始就说自己做了完整 long-term memory。
