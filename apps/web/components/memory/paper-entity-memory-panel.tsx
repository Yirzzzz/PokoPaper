"use client";

import { useMemo, useState, useTransition } from "react";

import { fetchPaperEntityMemories } from "@/lib/api/client";
import type { PaperEntityMemoryCard } from "@/types";

type PaperEntityMemoryPanelProps = {
  initialItems: PaperEntityMemoryCard[];
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

function DetailBlock({
  title,
  content,
}: {
  title: string;
  content: string;
}) {
  return (
    <section className="rounded-3xl border border-black/10 bg-white/50 p-4">
      <p className="text-xs uppercase tracking-[0.24em] text-slate-500">{title}</p>
      <div className="mt-3 text-sm leading-7 text-slate-800">{content || "当前没有内容。"}</div>
    </section>
  );
}

export function PaperEntityMemoryPanel({ initialItems }: PaperEntityMemoryPanelProps) {
  const [items, setItems] = useState(initialItems);
  const [selectedPaperId, setSelectedPaperId] = useState<string | null>(initialItems[0]?.paper_id ?? null);
  const [isPending, startTransition] = useTransition();

  const selectedItem = useMemo(
    () => items.find((item) => item.paper_id === selectedPaperId) ?? items[0] ?? null,
    [items, selectedPaperId],
  );

  const refresh = () =>
    startTransition(async () => {
      const response = await fetchPaperEntityMemories();
      setItems(response.items);
      setSelectedPaperId((current) =>
        response.items.some((item) => item.paper_id === current) ? current : response.items[0]?.paper_id ?? null,
      );
    });

  return (
    <div className="grid gap-4 xl:grid-cols-[360px_minmax(0,1fr)]">
      <aside className="glass-panel flex min-h-[640px] flex-col gap-4 p-4">
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="text-xs uppercase tracking-[0.24em] text-brand">论文记忆</p>
            <h2 className="mt-2 text-lg font-semibold text-slate-900">Paper Cards</h2>
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
              当前还没有论文实体记忆卡片。
            </div>
          ) : null}
          {items.map((item) => {
            const selected = item.paper_id === selectedItem?.paper_id;
            return (
              <button
                key={item.paper_id}
                type="button"
                onClick={() => setSelectedPaperId(item.paper_id)}
                className={`w-full rounded-3xl border px-4 py-4 text-left ${
                  selected ? "border-brand/40 bg-brand/10" : "border-black/10 bg-white/55"
                }`}
              >
                <p className="text-sm font-medium text-slate-900">{item.paper_title}</p>
                <p className="mt-2 line-clamp-4 text-sm leading-6 text-slate-700">{item.summary_card}</p>
                <div className="mt-3 flex flex-wrap gap-2">
                  {item.keywords.slice(0, 3).map((keyword) => (
                    <span
                      key={`${item.paper_id}:${keyword}`}
                      className="rounded-full border border-black/10 bg-white/80 px-2 py-1 text-xs text-slate-700"
                    >
                      {keyword}
                    </span>
                  ))}
                </div>
                <p className="mt-3 text-xs text-slate-500">{formatDate(item.updated_at)}</p>
              </button>
            );
          })}
        </div>
      </aside>

      <section className="glass-panel min-h-[640px] p-6">
        {!selectedItem ? (
          <div className="flex h-full items-center justify-center text-sm text-slate-600">
            当前还没有可查看的论文实体记忆。
          </div>
        ) : (
          <div className="space-y-6">
            <div>
              <p className="text-xs uppercase tracking-[0.24em] text-brand">Paper Entity Memory</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-900">{selectedItem.paper_title}</h2>
              <div className="mt-3 space-y-1 text-sm text-slate-700">
                <div>paper_id: {selectedItem.paper_id}</div>
                <div>updated_at: {formatDate(selectedItem.updated_at)}</div>
              </div>
            </div>

            <section className="rounded-[28px] border border-brand/15 bg-gradient-to-br from-amber-50 via-white to-sky-50 p-5">
              <p className="text-xs uppercase tracking-[0.24em] text-slate-500">Summary Card</p>
              <p className="mt-4 text-sm leading-8 text-slate-900">{selectedItem.summary_card}</p>
            </section>

            <div className="grid gap-4 lg:grid-cols-2">
              <DetailBlock title="Motivation" content={selectedItem.motivation} />
              <DetailBlock title="Problem" content={selectedItem.problem} />
              <DetailBlock title="Core Proposal" content={selectedItem.core_proposal} />
              <DetailBlock title="Method" content={selectedItem.method} />
              <DetailBlock title="Value" content={selectedItem.value} />
              <DetailBlock title="Resolved Gap" content={selectedItem.resolved_gap} />
              <DetailBlock title="Test Data / Evidence" content={selectedItem.test_data} />
              <DetailBlock title="Key Results" content={selectedItem.key_results} />
            </div>

            <section className="rounded-3xl border border-black/10 bg-white/50 p-4">
              <p className="text-xs uppercase tracking-[0.24em] text-slate-500">Keywords</p>
              <div className="mt-3 flex flex-wrap gap-2">
                {selectedItem.keywords.length === 0 ? (
                  <span className="text-sm text-slate-600">当前没有关键词。</span>
                ) : (
                  selectedItem.keywords.map((keyword) => (
                    <span
                      key={`${selectedItem.paper_id}:detail:${keyword}`}
                      className="rounded-full border border-black/10 bg-white/85 px-3 py-2 text-sm text-slate-800"
                    >
                      {keyword}
                    </span>
                  ))
                )}
              </div>
            </section>
          </div>
        )}
      </section>
    </div>
  );
}
