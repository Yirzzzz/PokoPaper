# Memory Store Lock Interview Q&A

## 1. 这个问题是什么？

项目里有一个本地 JSON 存储文件 `store.json`，会被多个接口同时读写。

在“记忆中心”页面里，服务端会并发请求多个 memory 接口，例如：

- `/memory/user`
- `/memory/session-memories`
- `/memory/session-summaries`
- `/memory/paper-entities`

如果用户频繁切换导航，这些请求会在很短时间内重复触发。  
原来的本地存储实现没有真正做到“跨请求串行化读写”，所以会出现随机 500。

---

## 2. 为什么原来的实现会报错？

根因不是单个接口逻辑错，而是并发读写同一个 `store.json` 时存在竞态。

原来的实现里：

- `get_repository()` 每次调用都会新建一个 `LocalStoreRepository`
- `LocalStoreRepository` 在 `__init__` 里创建的是实例级 `Lock()`

这意味着：

- 请求 A 有自己的 repository 和自己的锁
- 请求 B 也有自己的 repository 和自己的锁

虽然每个实例“看起来有锁”，但它们不是同一把锁。  
所以多个请求其实还是可以同时操作同一个 `store.json`。

典型风险有两个：

1. 一个请求正在写文件，另一个请求同时读取
2. 两个请求几乎同时写文件，后写入的内容覆盖先写入的内容，或者读取到不完整 JSON

这样就会导致：

- JSON 解析失败
- 响应模型校验失败
- 某个 memory 接口随机返回 500
- 前端在服务端渲染时看到 `Request failed: /memory/paper-entities`

---

## 3. 为什么这里一定要加锁？

因为这是一个“共享单文件存储”的场景。

只要多个请求会同时访问同一个文件，就必须保证：

- 读和写不能互相打断
- 写和写不能交叉覆盖
- 一个完整版本写完之前，其他请求不能读到半成品

如果不加锁，系统在低并发时可能“看起来正常”，但一旦页面并发请求增多，问题就会随机暴露。  
这种问题最典型的特征就是：

- 难稳定复现
- 点几次导航才出现
- 重试又可能暂时恢复

---

## 4. 这次具体改了哪里？

核心改动在：

- [local_store.py](/Users/yirz/PyCharmProject/pokomon/apps/api/app/repositories/local_store.py)

### 改动 1：把实例级锁改成“按文件路径共享的类级锁”

原来：

- 每个 `LocalStoreRepository()` 都会创建自己的 `Lock()`

现在：

- `LocalStoreRepository` 维护一个类级 `_locks` 字典
- key 是 `db_path`
- 同一个 `store.json` 对应同一把锁

这意味着不管创建多少个 repository 实例，只要它们操作的是同一个 `store.json`，就会共用同一把锁。

这样不同请求之间就真正串行化了。

### 改动 2：写文件改成“临时文件 + 原子替换”

原来是直接：

- `write_text(store.json)`

现在改成：

1. 先写到 `store.tmp`
2. 再 `replace()` 原子替换成 `store.json`

这样可以避免读请求读到“只写了一半的 JSON 文件”。

---

## 5. 为什么改完之后就不会随机报错了？

因为现在两个关键风险都被处理掉了。

### 第一层：共享锁

共享锁保证：

- 同一时刻只有一个请求能读/写这个 JSON 文件
- 不会再出现多个实例各自拿着不同锁、实际上同时操作文件的情况

### 第二层：原子写入

原子替换保证：

- 文件写入对其他请求来说是“要么旧版本，要么新版本”
- 不会看到中间态

所以现在不会再因为导航跳转触发多个并发请求，而把 `store.json` 搞到不一致状态。

---

## 6. 这个问题在面试里可以怎么讲？

可以这样回答：

> 我们当时有一个本地 JSON 作为 memory store，前端“记忆中心”页面会并发请求多个 memory 接口。最开始 repository 虽然用了 `Lock`，但那个锁是实例级的，而 repository factory 每次请求都会 new 一个实例，所以实际上不同请求拿到的是不同的锁，并没有真正保护共享文件。这样在频繁导航或并发请求下，就会出现随机 500，本质是并发读写同一个 JSON 文件导致的竞态。  
> 后来我把它改成了按 `db_path` 共享的类级锁，确保所有请求操作同一个 `store.json` 时共用同一把锁；同时把写入方式改成先写临时文件再原子替换，避免读取到半写入状态。修完之后，这类随机错误就稳定消失了。

---

## 7. 这个方案的边界是什么？

这个方案适合当前项目阶段：

- 单机
- 本地文件存储
- 中低并发

它能显著提升稳定性，但不是最终形态。

如果系统继续扩大，下一步更合理的是：

- 把 memory store 迁到真正的数据库
- 或者至少把写入做成专门的持久化层

因为文件锁方案解决的是“当前架构下的并发安全”，不是从根上替代数据库。

---

## 8. 我还做了什么防护？

除了修后端并发锁，我还对前端 `/memory` 页做了容错：

- [page.tsx](/Users/yirz/PyCharmProject/pokomon/apps/web/app/(dashboard)/memory/page.tsx)

做法是把原来的 `Promise.all` 改成 `Promise.allSettled`。

这样即使某个子接口暂时失败，也不会让整个“记忆中心”页面直接崩掉。  
这不是根因修复，但它能提升页面健壮性。

---

## 9. 我怎么验证这个修复？

我做了两类验证：

### 自动化验证

- 后端测试：
  `PYTHONPATH=apps/api python -m unittest apps/api/tests/test_memory_scope.py`
- 前端构建：
  `npm run build`

并补了一条回归测试，确认：

- 不同 `LocalStoreRepository` 实例会共享同一把锁

### 手动验证

1. 启动后端
2. 打开 `/memory`
3. 在多个导航之间频繁切换
4. 重复进入“记忆中心”
5. 确认不会再随机出现 `Request failed: /memory/paper-entities`

---

## 10. 一句话总结

这次修复的核心不是“修某个接口”，而是把本地 JSON memory store 从“伪加锁”改成了“真正跨请求串行化 + 原子写入”，解决了频繁导航下的随机并发读写故障。
