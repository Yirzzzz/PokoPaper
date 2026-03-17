"use client";

import { useMemo, useState, useTransition } from "react";

import { fetchLongTermMemories } from "@/lib/api/client";
import type { LongTermMemoryItem } from "@/types";

type LongTermMemoryPanelProps = {
  initialItems: LongTermMemoryItem[];
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

function confidenceTone(value: number) {
  if (value >= 0.85) return "text-emerald-700";
  if (value >= 0.7) return "text-amber-700";
  return "text-slate-600";
}

export function LongTermMemoryPanel({ initialItems }: LongTermMemoryPanelProps) {
  const [items, setItems] = useState(initialItems);
  const [selectedId, setSelectedId] = useState<string | null>(initialItems[0]?.item_id ?? null);
  const [isPending, startTransition] = useTransition();

  const selectedItem = useMemo(
    () => items.find((item) => item.item_id === selectedId) ?? items[0] ?? null,
    [items, selectedId],
  );

  const refresh = () =>
    startTransition(async () => {
      const response = await fetchLongTermMemories();
      setItems(response.items);
      setSelectedId((current) =>
        response.items.some((item) => item.item_id === current) ? current : response.items[0]?.item_id ?? null,
      );
    });

  return (
    <div className="grid gap-4 xl:grid-cols-[360px_minmax(0,1fr)]">
      <aside className="glass-panel flex min-h-[720px] flex-col gap-4 p-4">
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="text-xs uppercase tracking-[0.24em] text-brand">Long-Term Memory</p>
            <h2 className="mt-2 text-lg font-semibold text-slate-900">统一长期记忆库</h2>
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

        <div className="space-y-3 overflow-y-auto">
          {items.length === 0 ? (
            <div className="rounded-3xl border border-dashed border-black/10 bg-white/40 px-4 py-6 text-sm text-slate-600">
              当前还没有被记录为长期记忆的对话内容。
            </div>
          ) : null}
          {items.map((item) => {
            const selected = item.item_id === selectedItem?.item_id;
            return (
              <button
                key={item.item_id}
                type="button"
                onClick={() => setSelectedId(item.item_id)}
                className={`w-full rounded-3xl border px-4 py-4 text-left ${
                  selected ? "border-brand/40 bg-brand/10" : "border-black/10 bg-white/55"
                }`}
              >
                <div className="flex items-center justify-between gap-3">
                  <p className="text-sm font-medium text-slate-900">{item.memory_type}</p>
                  <span className={`text-xs font-medium ${confidenceTone(item.confidence)}`}>
                    {item.confidence.toFixed(2)}
                  </span>
                </div>
                <p className="mt-2 text-xs uppercase tracking-[0.18em] text-slate-500">
                  {item.source_scope} {item.paper_title ? `· ${item.paper_title}` : ""}
                </p>
                <p className="mt-3 line-clamp-3 text-sm leading-6 text-slate-700">{item.memory_text}</p>
                <p className="mt-3 text-xs text-slate-500">{formatDate(item.updated_at)}</p>
              </button>
            );
          })}
        </div>
      </aside>

      <section className="glass-panel min-h-[720px] p-6">
        {!selectedItem ? (
          <div className="flex h-full items-center justify-center text-sm text-slate-600">
            当前还没有长期记忆内容。
          </div>
        ) : (
          <div className="space-y-6">
            <div>
              <p className="text-xs uppercase tracking-[0.24em] text-brand">Long-Term Memory Item</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-900">{selectedItem.memory_type}</h2>
              <div className="mt-3 space-y-1 text-sm text-slate-700">
                <div>source_scope: {selectedItem.source_scope}</div>
                <div>conversation: {selectedItem.conversation_title ?? selectedItem.conversation_id}</div>
                <div>paper: {selectedItem.paper_title ?? selectedItem.paper_id ?? "—"}</div>
                <div className={confidenceTone(selectedItem.confidence)}>confidence: {selectedItem.confidence.toFixed(2)}</div>
              </div>
            </div>

            <section className="rounded-[28px] border border-brand/15 bg-gradient-to-br from-amber-50 via-white to-sky-50 p-5">
              <p className="text-xs uppercase tracking-[0.24em] text-slate-500">Memory Text</p>
              <p className="mt-4 text-sm leading-8 text-slate-900">{selectedItem.memory_text}</p>
            </section>

            <div className="grid gap-4 lg:grid-cols-2">
              <section className="rounded-3xl border border-black/10 bg-white/50 p-4">
                <p className="text-xs uppercase tracking-[0.24em] text-slate-500">Question Preview</p>
                <p className="mt-3 text-sm leading-7 text-slate-800">
                  {String(selectedItem.metadata.question_preview ?? "—")}
                </p>
              </section>
              <section className="rounded-3xl border border-black/10 bg-white/50 p-4">
                <p className="text-xs uppercase tracking-[0.24em] text-slate-500">Answer Preview</p>
                <p className="mt-3 text-sm leading-7 text-slate-800">
                  {String(selectedItem.metadata.answer_preview ?? "—")}
                </p>
              </section>
              <section className="rounded-3xl border border-black/10 bg-white/50 p-4">
                <p className="text-xs uppercase tracking-[0.24em] text-slate-500">Why Stored</p>
                <p className="mt-3 text-sm leading-7 text-slate-800">
                  {String(selectedItem.metadata.reason ?? "—")}
                </p>
              </section>
              <section className="rounded-3xl border border-black/10 bg-white/50 p-4">
                <p className="text-xs uppercase tracking-[0.24em] text-slate-500">Metadata</p>
                <div className="mt-3 space-y-2 text-sm text-slate-800">
                  <div>source_type: {selectedItem.source_type}</div>
                  <div>confidence_level: {String(selectedItem.metadata.confidence_level ?? "—")}</div>
                  <div>evidence_count: {String(selectedItem.metadata.evidence_count ?? "—")}</div>
                  <div>trigger_signals: {Array.isArray(selectedItem.metadata.trigger_signals) ? selectedItem.metadata.trigger_signals.join(" / ") || "—" : "—"}</div>
                  <div>concepts: {Array.isArray(selectedItem.metadata.concepts) ? selectedItem.metadata.concepts.join(" / ") || "—" : "—"}</div>
                </div>
              </section>
            </div>
          </div>
        )}
      </section>
    </div>
  );
}
