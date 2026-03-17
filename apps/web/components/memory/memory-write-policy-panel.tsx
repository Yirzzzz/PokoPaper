"use client";

import { useMemo, useState, useTransition } from "react";

import { inspectMemoryWritePolicy } from "@/lib/api/client";
import type {
  MemoryItem,
  MemoryWriteDecision,
  PaperCard,
  SessionMemoryView,
} from "@/types";

type MemoryWritePolicyPanelProps = {
  papers: PaperCard[];
  sessions: SessionMemoryView[];
  initialMemoryItems: MemoryItem[];
};

function formatDate(value?: string | null) {
  if (!value) return "—";
  return new Date(value).toLocaleString("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function renderValue(value: unknown) {
  if (value == null) return "—";
  if (typeof value === "string") return value;
  return JSON.stringify(value, null, 2);
}

export function MemoryWritePolicyPanel({
  papers,
  sessions,
  initialMemoryItems,
}: MemoryWritePolicyPanelProps) {
  const [sourceType, setSourceType] = useState<"dialog" | "overview">("dialog");
  const [paperId, setPaperId] = useState<string>(papers[0]?.id ?? "");
  const [sessionId, setSessionId] = useState<string>(sessions[0]?.conversation_id ?? "");
  const [question, setQuestion] = useState("我没懂 Retrieval 方法，能解释一下这篇论文的方法吗？");
  const [answer, setAnswer] = useState("当然可以，我先讲方法主线，再说明为什么它有效。");
  const [decision, setDecision] = useState<MemoryWriteDecision | null>(null);
  const [error, setError] = useState<string>("");
  const [isPending, startTransition] = useTransition();

  const debugItems = useMemo(
    () =>
      initialMemoryItems
        .filter(
          (item) =>
            !!(item.target_field || item.source_type || item.operation) &&
            !!(item.source_question || item.source_answer_preview),
        )
        .sort((a, b) => {
          const left = b.updated_at ?? "";
          const right = a.updated_at ?? "";
          return left.localeCompare(right);
        })
        .slice(0, 12),
    [initialMemoryItems],
  );

  const runInspect = () =>
    startTransition(async () => {
      setError("");
      try {
        const result = await inspectMemoryWritePolicy({
          source_type: sourceType,
          paper_id: paperId || null,
          session_id: sourceType === "dialog" ? sessionId || null : null,
          question,
          answer: sourceType === "dialog" ? answer : null,
        });
        setDecision(result.decision);
      } catch (inspectError) {
        setError(inspectError instanceof Error ? inspectError.message : "Inspect failed");
      }
    });

  return (
    <div className="grid gap-4 xl:grid-cols-[420px_minmax(0,1fr)]">
      <aside className="glass-panel flex min-h-[720px] flex-col gap-4 p-5">
        <div>
          <p className="text-xs uppercase tracking-[0.24em] text-brand">Write Policy</p>
          <h2 className="mt-2 text-xl font-semibold text-slate-900">策略调试台</h2>
          <p className="mt-2 text-sm leading-6 text-slate-700">
            输入一段对话或 overview 场景，查看系统是否会把它提升为长期记忆，以及会写到哪一层。
          </p>
        </div>

        <label className="space-y-2 text-sm text-slate-700">
          <span className="block text-xs uppercase tracking-[0.2em] text-slate-500">Source Type</span>
          <select
            value={sourceType}
            onChange={(event) => setSourceType(event.target.value as "dialog" | "overview")}
            className="w-full rounded-2xl border border-black/10 bg-white/80 px-3 py-3 text-sm text-slate-900 outline-none"
          >
            <option value="dialog">dialog</option>
            <option value="overview">overview</option>
          </select>
        </label>

        <label className="space-y-2 text-sm text-slate-700">
          <span className="block text-xs uppercase tracking-[0.2em] text-slate-500">Paper</span>
          <select
            value={paperId}
            onChange={(event) => setPaperId(event.target.value)}
            className="w-full rounded-2xl border border-black/10 bg-white/80 px-3 py-3 text-sm text-slate-900 outline-none"
          >
            {papers.map((paper) => (
              <option key={paper.id} value={paper.id}>
                {paper.title}
              </option>
            ))}
          </select>
        </label>

        {sourceType === "dialog" ? (
          <label className="space-y-2 text-sm text-slate-700">
            <span className="block text-xs uppercase tracking-[0.2em] text-slate-500">Conversation</span>
            <select
              value={sessionId}
              onChange={(event) => setSessionId(event.target.value)}
              className="w-full rounded-2xl border border-black/10 bg-white/80 px-3 py-3 text-sm text-slate-900 outline-none"
            >
              {sessions.map((session) => (
                <option key={session.conversation_id} value={session.conversation_id}>
                  {session.title}
                </option>
              ))}
            </select>
          </label>
        ) : null}

        <label className="space-y-2 text-sm text-slate-700">
          <span className="block text-xs uppercase tracking-[0.2em] text-slate-500">Question / Input</span>
          <textarea
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            rows={5}
            className="w-full rounded-3xl border border-black/10 bg-white/80 px-4 py-4 text-sm leading-7 text-slate-900 outline-none"
          />
        </label>

        {sourceType === "dialog" ? (
          <label className="space-y-2 text-sm text-slate-700">
            <span className="block text-xs uppercase tracking-[0.2em] text-slate-500">Answer</span>
            <textarea
              value={answer}
              onChange={(event) => setAnswer(event.target.value)}
              rows={4}
              className="w-full rounded-3xl border border-black/10 bg-white/80 px-4 py-4 text-sm leading-7 text-slate-900 outline-none"
            />
          </label>
        ) : null}

        <button
          type="button"
          onClick={runInspect}
          disabled={isPending}
          className="rounded-full bg-slate-900 px-5 py-3 text-sm font-medium text-white"
        >
          {isPending ? "分析中..." : "Inspect Decision"}
        </button>

        {error ? <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</div> : null}
      </aside>

      <section className="space-y-4">
        <div className="glass-panel min-h-[360px] p-6">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-xs uppercase tracking-[0.24em] text-brand">Decision</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-900">结构化写入结果</h2>
            </div>
            {decision ? (
              <div className="rounded-2xl border border-black/10 bg-white/70 px-4 py-3 text-sm text-slate-700">
                <div>should_write: {String(decision.should_write)}</div>
                <div>threshold: {decision.threshold.toFixed(2)}</div>
                <div>reason: {decision.reason ?? "—"}</div>
              </div>
            ) : null}
          </div>

          {!decision ? (
            <div className="mt-8 flex h-[220px] items-center justify-center rounded-3xl border border-dashed border-black/10 bg-white/40 text-sm text-slate-600">
              运行 inspect 后，这里会显示结构化 MemoryWriteDecision。
            </div>
          ) : (
            <div className="mt-6 space-y-4">
              {decision.writes.length === 0 ? (
                <div className="rounded-3xl border border-dashed border-black/10 bg-white/40 px-4 py-6 text-sm text-slate-600">
                  当前没有候选写入动作。
                </div>
              ) : (
                decision.writes.map((write, index) => (
                  <article
                    key={`${write.target_scope}:${write.target_field}:${index}`}
                    className="rounded-3xl border border-black/10 bg-white/70 p-5"
                  >
                    <div className="flex flex-wrap items-center gap-2 text-xs uppercase tracking-[0.18em] text-slate-500">
                      <span>{write.target_scope}</span>
                      <span>/</span>
                      <span>{write.target_field}</span>
                      <span>/</span>
                      <span>{write.operation}</span>
                    </div>
                    <div className="mt-3 grid gap-4 lg:grid-cols-[minmax(0,1fr)_220px]">
                      <div className="space-y-3">
                        <p className="text-sm leading-7 text-slate-800">{write.reason}</p>
                        <pre className="overflow-x-auto rounded-2xl bg-slate-950/95 p-4 text-xs leading-6 text-slate-100">
                          {renderValue(write.value)}
                        </pre>
                      </div>
                      <div className="rounded-2xl border border-black/10 bg-slate-50 p-4 text-sm leading-7 text-slate-700">
                        <div>confidence: {write.confidence.toFixed(2)}</div>
                        <div>evidence_count: {write.evidence_count}</div>
                        <div>source_type: {write.source_type}</div>
                        <div>updated_at: {formatDate(write.last_updated_at)}</div>
                      </div>
                    </div>
                  </article>
                ))
              )}
            </div>
          )}
        </div>

        <div className="glass-panel p-6">
          <div>
            <p className="text-xs uppercase tracking-[0.24em] text-brand">Promoted Memories</p>
            <h2 className="mt-2 text-xl font-semibold text-slate-900">被提升为长期记忆的会话内容</h2>
            <p className="mt-2 text-sm leading-6 text-slate-700">
              这里只展示已经真正落库的长期记忆片段，也就是“某个会话里值得被长期记住的内容”。
            </p>
          </div>

          <div className="mt-5 space-y-3">
            {debugItems.length === 0 ? (
              <div className="rounded-3xl border border-dashed border-black/10 bg-white/40 px-4 py-6 text-sm text-slate-600">
                当前还没有被提升为长期记忆的会话内容。
              </div>
            ) : (
              debugItems.map((item) => (
                <article
                  key={item.memory_id}
                  className="rounded-3xl border border-black/10 bg-white/70 p-4"
                >
                  <div className="flex flex-wrap items-center gap-2 text-xs uppercase tracking-[0.18em] text-slate-500">
                    <span>{item.target_scope ?? item.scope}</span>
                    <span>/</span>
                    <span>{item.target_field ?? item.memory_type}</span>
                    <span>/</span>
                    <span>{item.operation ?? "persisted"}</span>
                  </div>
                  <div className="mt-3 grid gap-3 lg:grid-cols-[minmax(0,1fr)_260px]">
                    <div className="space-y-3">
                      <div className="rounded-2xl border border-black/10 bg-white/85 p-4">
                        <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Source Question</p>
                        <p className="mt-2 text-sm leading-7 text-slate-900">
                          {item.source_question ?? "—"}
                        </p>
                      </div>

                      {item.source_answer_preview ? (
                        <div className="rounded-2xl border border-black/10 bg-white/85 p-4">
                          <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Answer Preview</p>
                          <p className="mt-2 text-sm leading-7 text-slate-800">
                            {item.source_answer_preview}
                          </p>
                        </div>
                      ) : null}

                      <div className="rounded-2xl border border-black/10 bg-amber-50/70 p-4">
                        <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Why It Was Stored</p>
                        <div className="mt-2 text-sm font-medium text-slate-900">{item.summary}</div>
                        <div className="mt-2 text-sm leading-7 text-slate-700">{item.write_reason ?? "—"}</div>
                      </div>
                    </div>
                    <div className="rounded-2xl border border-black/10 bg-slate-50 p-4 text-sm leading-7 text-slate-700">
                      <div>confidence: {item.write_confidence?.toFixed(2) ?? "—"}</div>
                      <div>source_type: {item.source_type ?? "—"}</div>
                      <div>evidence_count: {item.evidence_count ?? "—"}</div>
                      <div>target_scope: {item.target_scope ?? item.scope}</div>
                      <div>target_field: {item.target_field ?? item.memory_type}</div>
                      <div>operation: {item.operation ?? "persisted"}</div>
                      <div>updated_at: {formatDate(item.updated_at)}</div>
                    </div>
                  </div>
                </article>
              ))
            )}
          </div>
        </div>
      </section>
    </div>
  );
}
