"use client";

import { useState, useTransition } from "react";

import { fetchPapers, fetchUserEntityMemory } from "@/lib/api/client";
import type { PaperCard, UserEntityMemory } from "@/types";

type EntityMemoryPanelProps = {
  initialMemory: UserEntityMemory;
  initialPapers: PaperCard[];
};

function MemoryList({
  title,
  emptyLabel,
  items,
}: {
  title: string;
  emptyLabel: string;
  items: string[];
}) {
  return (
    <section className="rounded-3xl border border-black/10 bg-white/50 p-4">
      <p className="text-xs uppercase tracking-[0.24em] text-slate-500">{title}</p>
      {items.length === 0 ? (
        <p className="mt-3 text-sm text-slate-600">{emptyLabel}</p>
      ) : (
        <div className="mt-3 flex flex-wrap gap-2">
          {items.map((item) => (
            <span
              key={item}
              className="rounded-full border border-black/10 bg-white/80 px-3 py-2 text-sm text-slate-800"
            >
              {item}
            </span>
          ))}
        </div>
      )}
    </section>
  );
}

export function EntityMemoryPanel({
  initialMemory,
  initialPapers,
}: EntityMemoryPanelProps) {
  const [memory, setMemory] = useState(initialMemory);
  const [papers, setPapers] = useState(initialPapers);
  const [isPending, startTransition] = useTransition();

  const paperTitleMap = new Map(papers.map((paper) => [paper.id, paper.title]));

  const refresh = () =>
    startTransition(async () => {
      const [nextMemory, nextPapers] = await Promise.all([
        fetchUserEntityMemory(),
        fetchPapers(),
      ]);
      setMemory(nextMemory);
      setPapers(nextPapers);
    });

  return (
    <div className="grid gap-4 xl:grid-cols-[320px_minmax(0,1fr)]">
      <aside className="glass-panel flex min-h-[640px] flex-col gap-4 p-4">
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="text-xs uppercase tracking-[0.24em] text-brand">实体记忆</p>
            <h2 className="mt-2 text-lg font-semibold text-slate-900">User Entity</h2>
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

        <div className="space-y-4 text-sm text-slate-700">
          <div className="rounded-3xl border border-black/10 bg-white/55 px-4 py-4">
            <div>user_id: {memory.user_id}</div>
            <div className="mt-2">scope: {memory.scope_type}</div>
            <div className="mt-2">已读论文: {memory.read_paper_ids.length}</div>
          </div>

          <div className="rounded-3xl border border-black/10 bg-white/55 px-4 py-4">
            <p className="text-xs uppercase tracking-[0.24em] text-slate-500">更新来源</p>
            <div className="mt-3 space-y-2 text-sm">
              <div>上传/解析驱动: read_paper_ids, recent_topics, paper_link_candidates</div>
              <div>对话驱动: weak_concepts, mastered_concepts, preferred_explanation_style, cross_paper_links</div>
            </div>
          </div>
        </div>
      </aside>

      <section className="glass-panel min-h-[640px] p-6">
        <div className="space-y-6">
          <div>
            <p className="text-xs uppercase tracking-[0.24em] text-brand">Entity Memory</p>
            <h2 className="mt-2 text-2xl font-semibold text-slate-900">用户实体记忆</h2>
            <p className="mt-3 text-sm text-slate-700">
              这里展示的是用户级实体记忆，不包含当前 conversation 的短期上下文。
            </p>
          </div>

          <div className="grid gap-4 lg:grid-cols-2">
            <section className="rounded-3xl border border-black/10 bg-white/50 p-4">
              <p className="text-xs uppercase tracking-[0.24em] text-slate-500">Upload / Parse Driven</p>
              <div className="mt-4 space-y-4">
                <div>
                  <p className="text-sm font-medium text-slate-900">Read Papers</p>
                  {memory.read_paper_ids.length === 0 ? (
                    <p className="mt-2 text-sm text-slate-600">当前还没有已读论文记录。</p>
                  ) : (
                    <div className="mt-3 space-y-2">
                      {memory.read_paper_ids.map((paperId) => (
                        <div
                          key={paperId}
                          className="rounded-2xl border border-black/10 bg-white/75 px-3 py-3 text-sm text-slate-800"
                        >
                          <div className="font-medium text-slate-900">
                            {paperTitleMap.get(paperId) ?? paperId}
                          </div>
                          <div className="mt-1 text-xs text-slate-500">{paperId}</div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                <MemoryList
                  title="Recent Topics"
                  emptyLabel="当前还没有 recent_topics。"
                  items={memory.recent_topics}
                />

                <section className="rounded-3xl border border-black/10 bg-white/50 p-4">
                  <p className="text-xs uppercase tracking-[0.24em] text-slate-500">Paper Link Candidates</p>
                  {memory.paper_link_candidates.length === 0 ? (
                    <p className="mt-3 text-sm text-slate-600">当前没有候选跨论文关联。</p>
                  ) : (
                    <div className="mt-3 space-y-2">
                      {memory.paper_link_candidates.map((item) => (
                        <div
                          key={`${item.source_paper_id}:${item.target_paper_id}`}
                          className="rounded-2xl border border-black/10 bg-white/75 px-3 py-3 text-sm text-slate-800"
                        >
                          <div className="font-medium text-slate-900">{item.target_paper_id}</div>
                          <div className="mt-1 text-xs text-slate-500">
                            from {paperTitleMap.get(item.source_paper_id) ?? item.source_paper_id} · {item.relation}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </section>
              </div>
            </section>

            <section className="rounded-3xl border border-black/10 bg-white/50 p-4">
              <p className="text-xs uppercase tracking-[0.24em] text-slate-500">Conversation Driven</p>
              <div className="mt-4 space-y-4">
                <section className="rounded-3xl border border-black/10 bg-white/50 p-4">
                  <p className="text-xs uppercase tracking-[0.24em] text-slate-500">Preferred Style</p>
                  <div className="mt-3 rounded-2xl border border-black/10 bg-white/75 px-3 py-3 text-sm text-slate-800">
                    {memory.preferred_explanation_style || "intuitive_then_formula"}
                  </div>
                </section>

                <MemoryList
                  title="Weak Concepts"
                  emptyLabel="当前还没有 weak_concepts。"
                  items={memory.weak_concepts}
                />

                <MemoryList
                  title="Mastered Concepts"
                  emptyLabel="当前还没有 mastered_concepts。"
                  items={memory.mastered_concepts}
                />

                <section className="rounded-3xl border border-black/10 bg-white/50 p-4">
                  <p className="text-xs uppercase tracking-[0.24em] text-slate-500">Confirmed Cross-Paper Links</p>
                  {memory.cross_paper_links.length === 0 ? (
                    <p className="mt-3 text-sm text-slate-600">当前没有已确认的跨论文关联。</p>
                  ) : (
                    <div className="mt-3 space-y-2">
                      {memory.cross_paper_links.map((item) => (
                        <div
                          key={`${item.source_paper_id}:${item.target_paper_id}`}
                          className="rounded-2xl border border-black/10 bg-white/75 px-3 py-3 text-sm text-slate-800"
                        >
                          <div className="font-medium text-slate-900">{item.target_paper_id}</div>
                          <div className="mt-1 text-xs text-slate-500">
                            from {paperTitleMap.get(item.source_paper_id) ?? item.source_paper_id} · {item.relation}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </section>
              </div>
            </section>
          </div>
        </div>
      </section>
    </div>
  );
}
