"use client";

import { useMemo, useState, useTransition } from "react";

import { clearSessionMemory, fetchSessionMemories } from "@/lib/api/client";
import type { SessionMemoryView } from "@/types";

type SessionMemoryPanelProps = {
  initialItems: SessionMemoryView[];
};

function formatDate(value: string) {
  if (!value) return "—";
  return new Date(value).toLocaleString("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function SessionMemoryPanel({ initialItems }: SessionMemoryPanelProps) {
  const [items, setItems] = useState(initialItems);
  const [selectedConversationId, setSelectedConversationId] = useState<string | null>(
    initialItems[0]?.conversation_id ?? null,
  );
  const [isPending, startTransition] = useTransition();

  const selectedItem = useMemo(
    () => items.find((item) => item.conversation_id === selectedConversationId) ?? items[0] ?? null,
    [items, selectedConversationId],
  );

  const refresh = () =>
    startTransition(async () => {
      const response = await fetchSessionMemories();
      setItems(response.items);
      setSelectedConversationId((current) =>
        response.items.some((item) => item.conversation_id === current)
          ? current
          : response.items[0]?.conversation_id ?? null,
      );
    });

  const handleClear = (conversationId: string) =>
    startTransition(async () => {
      const cleared = await clearSessionMemory(conversationId);
      setItems((current) =>
        current.map((item) =>
          item.conversation_id === conversationId ? cleared : item,
        ),
      );
      setSelectedConversationId(conversationId);
    });

  return (
    <div className="grid gap-4 xl:grid-cols-[320px_minmax(0,1fr)]">
      <aside className="glass-panel flex min-h-[640px] flex-col gap-4 p-4">
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="text-xs uppercase tracking-[0.24em] text-brand">瞬时记忆</p>
            <h2 className="mt-2 text-lg font-semibold text-slate-900">Conversations</h2>
          </div>
          <button
            type="button"
            onClick={refresh}
            disabled={isPending}
            className="rounded-full border border-black/10 bg-white/70 px-4 py-2 text-sm text-slate-900"
          >
            刷新
          </button>
        </div>
        <div className="space-y-2 overflow-y-auto">
          {items.length === 0 ? (
            <div className="rounded-3xl border border-dashed border-black/10 bg-white/40 px-4 py-6 text-sm text-slate-600">
              当前还没有 conversation。
            </div>
          ) : null}
          {items.map((item) => {
            const selected = item.conversation_id === selectedItem?.conversation_id;
            return (
              <button
                key={item.conversation_id}
                type="button"
                onClick={() => setSelectedConversationId(item.conversation_id)}
                className={`w-full rounded-3xl border px-4 py-3 text-left ${
                  selected ? "border-brand/40 bg-brand/10" : "border-black/10 bg-white/55"
                }`}
              >
                <p className="text-sm font-medium text-slate-900">{item.title}</p>
                <p className="mt-1 text-xs text-slate-600">
                  {item.conversation_type} {item.paper_title ? `· ${item.paper_title}` : ""}
                </p>
                <p className="mt-2 text-xs text-slate-500">
                  {item.is_empty ? "empty" : `${item.recent_messages_count} messages`} · {formatDate(item.updated_at)}
                </p>
              </button>
            );
          })}
        </div>
      </aside>

      <section className="glass-panel min-h-[640px] p-6">
        {!selectedItem ? (
          <div className="flex h-full items-center justify-center text-sm text-slate-600">
            请选择一个 conversation。
          </div>
        ) : (
          <div className="space-y-6">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-xs uppercase tracking-[0.24em] text-brand">Instant Memory</p>
                <h2 className="mt-2 text-2xl font-semibold text-slate-900">{selectedItem.title}</h2>
                <div className="mt-3 space-y-1 text-sm text-slate-700">
                  <div>conversation_id: {selectedItem.conversation_id}</div>
                  <div>conversation_type: {selectedItem.conversation_type}</div>
                  <div>paper_id: {selectedItem.paper_id ?? "—"}</div>
                  <div>updated_at: {formatDate(selectedItem.updated_at)}</div>
                </div>
              </div>
              <button
                type="button"
                onClick={() => handleClear(selectedItem.conversation_id)}
                disabled={isPending}
                className="rounded-full border border-rose-200 bg-rose-50 px-4 py-2 text-sm text-rose-700"
              >
                清空瞬时记忆与最近消息
              </button>
            </div>

            <div className="grid gap-4 lg:grid-cols-2">
              <section className="rounded-3xl border border-black/10 bg-white/50 p-4">
                <p className="text-xs uppercase tracking-[0.24em] text-slate-500">Recent Questions</p>
                {selectedItem.recent_questions.length === 0 ? (
                  <p className="mt-3 text-sm text-slate-600">当前没有 recent_questions。</p>
                ) : (
                  <div className="mt-3 space-y-2">
                    {selectedItem.recent_questions.map((question, index) => (
                      <div
                        key={`${selectedItem.conversation_id}:question:${index}:${question}`}
                        className="rounded-2xl border border-black/10 bg-white/70 px-3 py-3 text-sm text-slate-800"
                      >
                        {question}
                      </div>
                    ))}
                  </div>
                )}
              </section>

              <section className="rounded-3xl border border-black/10 bg-white/50 p-4">
                <p className="text-xs uppercase tracking-[0.24em] text-slate-500">Rolling Summary</p>
                <div className="mt-3 rounded-2xl border border-black/10 bg-white/70 px-3 py-3 text-sm text-slate-800">
                  {selectedItem.rolling_summary || "当前没有 rolling_summary。"}
                </div>
              </section>
            </div>

            <section className="rounded-3xl border border-black/10 bg-white/50 p-4">
              <p className="text-xs uppercase tracking-[0.24em] text-slate-500">Recent Raw Messages</p>
              {selectedItem.recent_messages.length === 0 ? (
                <p className="mt-3 text-sm text-slate-600">当前 conversation 为空。</p>
              ) : (
                <div className="mt-3 space-y-3">
                  {selectedItem.recent_messages.map((message) => (
                    <div
                      key={message.message_id}
                      className={`rounded-2xl border px-4 py-3 text-sm ${
                        message.role === "user"
                          ? "border-emerald-200 bg-emerald-50 text-slate-900"
                          : "border-black/10 bg-white/80 text-slate-800"
                      }`}
                    >
                      <div className="mb-2 text-xs uppercase tracking-[0.18em] text-slate-500">
                        {message.role} · {formatDate(message.created_at)}
                      </div>
                      <div>{message.content_md}</div>
                    </div>
                  ))}
                </div>
              )}
            </section>
          </div>
        )}
      </section>
    </div>
  );
}
