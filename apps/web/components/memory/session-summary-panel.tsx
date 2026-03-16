"use client";

import { useMemo, useState, useTransition } from "react";

import { fetchSessionSummaries } from "@/lib/api/client";
import type { SessionSummaryView } from "@/types";

type SessionSummaryPanelProps = {
  initialItems: SessionSummaryView[];
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

function TagList({
  items,
  emptyLabel,
  keyPrefix,
}: {
  items: string[];
  emptyLabel: string;
  keyPrefix: string;
}) {
  if (items.length === 0) {
    return <p className="mt-3 text-sm text-slate-600">{emptyLabel}</p>;
  }

  return (
    <div className="mt-3 flex flex-wrap gap-2">
      {items.map((item, index) => (
        <span
          key={`${keyPrefix}:${index}:${item}`}
          className="rounded-full border border-black/10 bg-white/80 px-3 py-2 text-sm text-slate-800"
        >
          {item}
        </span>
      ))}
    </div>
  );
}

export function SessionSummaryPanel({ initialItems }: SessionSummaryPanelProps) {
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
      const response = await fetchSessionSummaries();
      setItems(response.items);
      setSelectedConversationId((current) =>
        response.items.some((item) => item.conversation_id === current)
          ? current
          : response.items[0]?.conversation_id ?? null,
      );
    });

  return (
    <div className="grid gap-4 xl:grid-cols-[320px_minmax(0,1fr)]">
      <aside className="glass-panel flex min-h-[640px] flex-col gap-4 p-4">
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="text-xs uppercase tracking-[0.24em] text-brand">短时记忆</p>
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
              当前还没有短时记忆内容。
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
                <p className="mt-2 line-clamp-3 text-xs leading-5 text-slate-500">
                  {item.summary_text || "当前还没有摘要内容。"}
                </p>
                <p className="mt-2 text-xs text-slate-500">
                  pending {item.pending_messages_count} · {formatDate(item.updated_at)}
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
            <div>
              <p className="text-xs uppercase tracking-[0.24em] text-brand">Short-Term Memory</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-900">{selectedItem.title}</h2>
              <div className="mt-3 space-y-1 text-sm text-slate-700">
                <div>conversation_id: {selectedItem.conversation_id}</div>
                <div>conversation_type: {selectedItem.conversation_type}</div>
                <div>paper_id: {selectedItem.paper_id ?? "—"}</div>
                <div>covered_message_until: {selectedItem.covered_message_until || "—"}</div>
                <div>last_updated_at: {formatDate(selectedItem.last_updated_at)}</div>
                <div>pending_messages: {selectedItem.pending_messages_count}</div>
              </div>
            </div>

            <section className="rounded-3xl border border-black/10 bg-white/50 p-4">
              <p className="text-xs uppercase tracking-[0.24em] text-slate-500">Summary Text</p>
              <div className="mt-3 rounded-2xl border border-black/10 bg-white/80 px-4 py-4 text-sm leading-7 text-slate-800">
                {selectedItem.summary_text || "当前还没有摘要内容。"}
              </div>
            </section>

            <div className="grid gap-4 lg:grid-cols-2">
              <section className="rounded-3xl border border-black/10 bg-white/50 p-4">
                <p className="text-xs uppercase tracking-[0.24em] text-slate-500">Discussion Topics</p>
                <TagList
                  items={selectedItem.discussion_topics}
                  emptyLabel="当前没有 discussion_topics。"
                  keyPrefix={`${selectedItem.conversation_id}:discussion_topics`}
                />
              </section>

              <section className="rounded-3xl border border-black/10 bg-white/50 p-4">
                <p className="text-xs uppercase tracking-[0.24em] text-slate-500">Open Questions</p>
                <TagList
                  items={selectedItem.open_questions}
                  emptyLabel="当前没有 open_questions。"
                  keyPrefix={`${selectedItem.conversation_id}:open_questions`}
                />
              </section>
            </div>

            <section className="rounded-3xl border border-black/10 bg-white/50 p-4">
              <p className="text-xs uppercase tracking-[0.24em] text-slate-500">Key Points</p>
              {selectedItem.key_points.length === 0 ? (
                <p className="mt-3 text-sm text-slate-600">当前没有 key_points。</p>
              ) : (
                <div className="mt-3 space-y-2">
                  {selectedItem.key_points.map((point, index) => (
                    <div
                      key={`${selectedItem.conversation_id}:key_point:${index}:${point}`}
                      className="rounded-2xl border border-black/10 bg-white/80 px-4 py-3 text-sm text-slate-800"
                    >
                      {point}
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
