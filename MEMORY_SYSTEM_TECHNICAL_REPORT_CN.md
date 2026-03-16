# 记忆系统技术报告

## 1. 项目背景

这个项目最初是一个论文阅读与问答系统，后面逐步演化出多类“记忆”能力，用来改善以下问题：

- 当前会话里，模型需要记住最近几轮上下文
- 用户在不同会话之间，希望保留稳定的阅读轨迹与理解状态
- 每篇论文本身，希望有一份可视化、可回忆的结构化卡片
- 不同场景下，记忆既要可查看，也要有清晰边界，避免串会话、串论文

在当前版本里，系统形成了四类记忆：

- 瞬时记忆
- 短时记忆
- 用户实体记忆
- 论文记忆

这些记忆已经统一接入前端“记忆中心”，同时后端也形成了比较清晰的数据模型和作用边界。

---

## 2. 目标与设计原则

这套记忆系统的核心目标，不是做一个无限扩张的“全知记忆框架”，而是解决真实交互中的几个基础问题：

1. 当前 conversation 的上下文不能丢
2. 不同 conversation 之间必须隔离
3. 用户长期背景可以跨会话共享
4. 每篇论文要有稳定的结构化知识卡片
5. prompt 接入要自然，不做僵硬的“问题分类框架”

几个重要设计原则如下：

- conversation isolation 优先
- 记忆按作用域分层
- 短期上下文和长期背景分开管理
- 用户记忆与论文记忆分开管理
- prompt 中把记忆作为辅助上下文，而不是显式路由规则

---

## 3. 系统总体结构

当前系统可以理解为三层：

### 3.1 会话层

定义在 conversation model 中：

- `global_chat`
- `paper_chat`

每个 conversation 有独立 `conversation_id`，消息历史按 `conversation_id` 隔离。

作用：

- 承载原始聊天记录
- 作为瞬时/短时记忆的边界

### 3.2 用户层

作用域是：

- `user:local-user`

作用：

- 保存用户跨会话共享的稳定背景
- 用于个性化解释和长期阅读轨迹

### 3.3 论文层

作用域是每篇论文独立的 `paper entity card`

作用：

- 保存论文本身的结构化概览
- 方便后续回忆“我读过哪篇论文、这篇论文主要讲什么”

---

## 4. 四类记忆的职责划分

### 4.1 瞬时记忆

本质上是一个窗口化上下文。

当前实现：

- 保留最近 `5` 组 QA
- 超出窗口后，最旧的 QA 从“瞬时上下文”中移出
- 但不会删除完整聊天存档

主要内容：

- 最近几轮 raw messages
- 最近 user questions

主要作用：

- 解决“我刚刚问了什么问题？”
- 解决“上一轮我们在说什么？”
- 给当前轮 prompt 提供最近上下文

### 4.2 短时记忆

短时记忆是对“窗口外历史”的压缩摘要。

当前实现：

- 最近 `8` 条 message 作为活跃窗口
- 超出窗口的旧消息进入待摘要缓冲
- 当缓冲累计 `4` 条 message 时，触发一次摘要更新
- 摘要采用“旧摘要 + 新过期消息”的增量更新

结构包括：

- `summary_text`
- `discussion_topics`
- `key_points`
- `open_questions`
- `last_updated_at`
- `covered_message_until`

主要作用：

- 不让窗口外历史完全丢失
- 用摘要形式保留更早讨论脉络
- 与 recent messages 一起进入 prompt

### 4.3 用户实体记忆

作用域：

- `user:local-user`

字段包括：

- `read_paper_ids`
- `recent_topics`
- `weak_concepts`
- `mastered_concepts`
- `preferred_explanation_style`
- `cross_paper_links`
- `paper_link_candidates`

更新来源分两类：

#### 上传/解析驱动更新

适合更新：

- `read_paper_ids`
- `recent_topics`
- `paper_link_candidates`

原因是这些信息属于“读过什么、最近在看什么”。

#### 对话驱动更新

适合更新：

- `weak_concepts`
- `mastered_concepts`
- `preferred_explanation_style`
- `cross_paper_links`

原因是这些信息更接近用户理解状态和偏好，不能只靠上传论文推断。

### 4.4 论文记忆

论文记忆不是 conversation memory，也不是 user memory，而是每篇论文一个独立的结构化卡片。

字段包括：

- `paper_id`
- `paper_title`
- `summary_card`
- `motivation`
- `problem`
- `core_proposal`
- `method`
- `value`
- `resolved_gap`
- `test_data`
- `key_results`
- `keywords`

生成时机：

- 论文上传成功
- 解析完成
- overview 生成后
- 自动生成论文记忆卡

主要作用：

- 用结构化形式存储论文主脉络
- 支持图鉴式回顾和可视化浏览

---

## 5. conversation model 是怎么支撑记忆边界的

这部分是整套系统能稳定运行的基础。

conversation model 的核心点：

- `conversation_id`
- `conversation_type`
  - `global_chat`
  - `paper_chat`
- `paper_id`
- `created_at`
- `updated_at`
- `is_deleted`

### 5.1 global chat

特点：

- 可以有多个独立 conversation
- 支持新建、切换、删除
- 不绑定具体论文

### 5.2 paper chat

特点：

- 每篇论文只有一个固定 conversation
- 只属于当前论文
- 不出现在主界面对战记录中

### 5.3 为什么这个模型重要

如果 conversation model 不稳定，就会出现：

- 主界面对话和论文页对话串联
- 会话历史被覆盖
- memory scope 绑定不清晰

所以 conversation model 重构是整个记忆系统的前提。

---

## 6. prompt 是怎么接入记忆的

### 6.1 设计原则

这里最关键的一个原则是：

不要把记忆做成“显式问题分类框架”。

也就是说，prompt 里没有这样的内容：

- 先判断问题属于哪一类
- 再决定是否使用某类记忆
- 如果记忆不足先解释不足

现在的做法是把记忆作为辅助上下文直接交给模型。

### 6.2 当前 prompt 的上下文块

当前主要接入两类：

#### 当前会话上下文

包括：

- recent messages
- session summary

作用：

- 帮模型理解当前 conversation 的最近脉络和更早摘要

#### 当前用户背景信息

包括：

- 已读论文
- 最近主题
- 薄弱概念
- 已掌握概念
- 偏好解释风格
- 已确认的跨论文关系

作用：

- 帮模型自然地个性化回答

### 6.3 为什么这样接

优点是：

- 更自然
- 不会让回答变得僵硬
- 减少 prompt 复杂度
- 模型在不相关时可以自动忽略

---

## 7. 后端实现链路

### 7.1 主要文件

conversation / chat:

- [chat.py](/Users/yirz/PyCharmProject/pokomon/apps/api/app/api/v1/chat.py)
- [local_store.py](/Users/yirz/PyCharmProject/pokomon/apps/api/app/repositories/local_store.py)

瞬时/短时记忆：

- [short_term_memory.py](/Users/yirz/PyCharmProject/pokomon/apps/api/app/services/short_term_memory.py)

用户实体记忆：

- [service.py](/Users/yirz/PyCharmProject/pokomon/apps/api/app/services/memory/service.py)

论文记忆：

- [paper_entity_memory.py](/Users/yirz/PyCharmProject/pokomon/apps/api/app/services/paper_entity_memory.py)

prompt 组装：

- [paper_analysis_prompt.py](/Users/yirz/PyCharmProject/pokomon/apps/api/app/agents/prompts/paper_analysis_prompt.py)
- [llm/service.py](/Users/yirz/PyCharmProject/pokomon/apps/api/app/services/llm/service.py)
- [rag/service.py](/Users/yirz/PyCharmProject/pokomon/apps/api/app/services/rag/service.py)

### 7.2 瞬时/短时记忆更新链路

在一次问答完成后：

1. 保存 raw messages
2. 更新当前 conversation 的瞬时记忆窗口
3. 检查是否有消息从窗口过期
4. 过期消息进入 `pending_messages`
5. 达到阈值后触发 session summary 增量更新
6. 新的 recent messages 和 session summary 供下一轮 prompt 使用

### 7.3 用户实体记忆更新链路

分两条：

#### 上传链路

在 ingestion 完成后：

1. 生成 overview
2. 更新 `read_paper_ids`
3. 更新 `recent_topics`
4. 更新 `paper_link_candidates`

#### 对话链路

在回答完成后：

1. 分析 question / answer 中的信号
2. 更新 `weak_concepts`
3. 更新 `mastered_concepts`
4. 更新 `preferred_explanation_style`
5. 如有明显证据，再更新 `cross_paper_links`

### 7.4 论文记忆生成链路

在论文 ingestion 阶段：

1. 解析论文
2. 生成 overview
3. 基于 overview 构建 `paper entity card`
4. 存储并供前端“论文记忆”页面展示

---

## 8. 前端是怎么可视化这些记忆的

当前前端已经统一成一个“记忆中心”。

入口：

- `/memory`

页面结构：

- 瞬时记忆
- 短时记忆
- 实体记忆
- 论文记忆

主要组件：

- [memory-center.tsx](/Users/yirz/PyCharmProject/pokomon/apps/web/components/memory/memory-center.tsx)
- [session-memory-panel.tsx](/Users/yirz/PyCharmProject/pokomon/apps/web/components/memory/session-memory-panel.tsx)
- [session-summary-panel.tsx](/Users/yirz/PyCharmProject/pokomon/apps/web/components/memory/session-summary-panel.tsx)
- [entity-memory-panel.tsx](/Users/yirz/PyCharmProject/pokomon/apps/web/components/memory/entity-memory-panel.tsx)
- [paper-entity-memory-panel.tsx](/Users/yirz/PyCharmProject/pokomon/apps/web/components/memory/paper-entity-memory-panel.tsx)

这个设计的价值在于：

- 调试方便
- 数据边界清楚
- 有利于理解不同记忆层的职责

---

## 9. 存储实现与一个真实工程问题

当前本地开发模式下，大部分结构化数据都放在一个 JSON 文件里：

- `storage/db/store.json`

里面集中存储：

- papers
- jobs
- overviews
- chat_sessions
- chat_messages
- memories
- paper_entity_cards

### 9.1 为什么这里会出问题

“记忆中心”页面会并发请求多个接口。  
原先 repository 虽然使用了 `Lock`，但锁是实例级的，而 repository 每次请求都会新建实例。结果就是：

- 不同请求实际上没有共享同一把锁
- 多个请求会并发读写同一个 `store.json`

这会导致随机 500。

### 9.2 我是怎么修的

修复方式：

- 把锁改成按 `db_path` 共享的类级锁
- 所有操作同一个 `store.json` 的 repository 实例共用同一把锁
- 文件写入改成“临时文件 + 原子替换”

这个修复点很有代表性，因为它体现了：

- 对共享资源并发问题的识别
- 对本地文件存储一致性的处理
- 对工程稳定性的优先级判断

---

## 10. 测试覆盖了什么

后端最小测试覆盖包括：

- 多个 global conversation 的创建、切换、删除
- paper chat 唯一性
- global / paper conversation 隔离
- 不同 paper conversation 隔离
- 瞬时记忆窗口更新
- 短时记忆增量摘要
- 用户实体记忆上传更新与对话更新
- 论文记忆卡生成
- prompt 注入不包含“先判断问题类型”的规则提示
- 本地存储共享锁回归测试

测试文件：

- [test_memory_scope.py](/Users/yirz/PyCharmProject/pokomon/apps/api/tests/test_memory_scope.py)
- [test_title_extraction.py](/Users/yirz/PyCharmProject/pokomon/apps/api/tests/test_title_extraction.py)

---

## 11. 这套系统的价值

从工程角度看，这套记忆系统的价值主要体现在三点：

### 11.1 数据边界变清楚了

不再是“所有上下文混成一个 session”。

而是明确区分：

- 当前会话上下文
- 当前会话较早摘要
- 全局用户背景
- 每篇论文的结构化知识卡

### 11.2 用户体验更自然

系统不再因为缺少显式 retrieval 命中就机械回答“没有历史记录”或“记忆不足”，而是通过当前 conversation 上下文自然回答。

### 11.3 以后扩展空间更大

虽然当前没有恢复完整长期 recall，但架构上已经预留了重新接入的空间：

- conversation scope 已清晰
- user scope 已清晰
- paper entity card 已清晰
- prompt 组装点已明确

以后接 RAG、跨论文召回、长期记忆管理，都更容易演进。

---

## 12. 如果写成简历，应该怎么写

### 12.1 简历版本一：偏系统设计

- 设计并实现分层记忆系统，将会话上下文拆分为瞬时记忆、短时摘要记忆、用户实体记忆和论文结构化记忆，建立 conversation、user、paper 三层作用域，提升多会话问答稳定性与上下文隔离性。

### 12.2 简历版本二：偏工程实现

- 重构论文问答系统的 conversation 与 memory 模型，支持多 global conversations、每篇论文唯一会话、窗口化上下文记忆、增量式会话摘要、用户画像记忆和论文记忆卡的可视化管理。

### 12.3 简历版本三：偏稳定性与落地

- 在本地文件存储模式下实现多层记忆管理与可视化页面，并修复共享 JSON store 的并发读写问题，通过共享锁与原子写入提升 memory center 页面稳定性。

### 12.4 面试口述版本

可以这样说：

> 我在项目里做了一套分层记忆系统。最底层先把会话模型梳理清楚，保证 global chat 和 paper chat 隔离；在这个基础上，我做了窗口化的瞬时记忆和增量摘要式短时记忆，让模型既能看最近几轮 raw messages，又能保留更早历史的压缩信息。然后我把用户长期稳定信息抽成 user entity memory，把每篇论文的核心脉络抽成 paper entity card，并统一做了可视化页面。整个 prompt 接入我刻意避免做成僵硬的分类路由，而是把记忆作为辅助上下文自然交给模型使用。

---

## 13. 写简历时不要夸大的点

为了保持真实，下面这些点最好不要写得过头：

- 不要写成“完整长期记忆平台”
- 不要写成“成熟的向量检索/跨论文推理系统”
- 不要写成“多用户画像系统”
- 不要写成“生产级高并发分布式 memory architecture”

更准确的说法是：

- 做了分层记忆系统原型
- 做了 conversation / user / paper 三层 memory scope
- 做了短期上下文、摘要记忆、实体记忆和论文记忆卡
- 做了 prompt 接入和可视化管理

---

## 14. 总结

这套记忆系统的关键，不在于“记忆越多越好”，而在于把不同类型的记忆拆清楚：

- 哪些只属于当前 conversation
- 哪些跨 conversation 共享
- 哪些属于某篇论文本身
- 哪些应该直接进 prompt
- 哪些只适合可视化管理，不适合硬塞进 prompt

从实现角度看，这个项目已经完成了一个比较完整的第一阶段：

- 会话隔离
- 窗口记忆
- 摘要记忆
- 用户实体记忆
- 论文记忆卡
- 记忆中心可视化
- 基础工程稳定性修复

如果以后继续迭代，最自然的方向会是：

- 单论文 RAG
- 更稳定的 paper recall
- 更精细的 memory update policy
- 从本地 JSON store 迁移到数据库/专门存储层
