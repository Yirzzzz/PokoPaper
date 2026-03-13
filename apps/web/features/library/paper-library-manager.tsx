"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";

import { deletePaper, updatePaperMetadata } from "@/lib/api/client";
import type { PaperCard } from "@/types";

type PaperLibraryManagerProps = {
  papers: PaperCard[];
};

export function PaperLibraryManager({ papers }: PaperLibraryManagerProps) {
  const router = useRouter();
  const [editingPaperId, setEditingPaperId] = useState<string | null>(null);
  const [categoryDraft, setCategoryDraft] = useState("");
  const [tagsDraft, setTagsDraft] = useState("");
  const [isPending, startTransition] = useTransition();

  return (
    <div className="mt-5 grid gap-4">
      {papers.length === 0 ? (
        <div className="rounded-3xl border border-dashed border-white/10 bg-white/5 p-5 text-sm text-mist">
          还没有论文。先上传一篇 PDF。
        </div>
      ) : (
        papers.map((paper) => {
          const isEditing = editingPaperId === paper.id;
          return (
            <div key={paper.id} className="rounded-3xl border border-white/10 bg-white/5 p-5">
              <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
                <Link href={`/papers/${paper.id}`} className="block min-w-0 flex-1">
                  <h4 className="text-lg font-medium text-white">{paper.title}</h4>
                  <div className="mt-3 flex flex-wrap gap-2 text-xs text-mist">
                    <span className="rounded-full border border-white/10 px-3 py-1.5">
                      {paper.authors.slice(0, 2).join(", ") || "Unknown"}
                    </span>
                    <span className="rounded-full border border-white/10 px-3 py-1.5">
                      {paper.status}
                    </span>
                    {paper.category ? (
                      <span className="rounded-full border border-brand/20 bg-brand/10 px-3 py-1.5 text-brand">
                        {paper.category}
                      </span>
                    ) : null}
                    {(paper.tags ?? []).map((tag) => (
                      <span key={`${paper.id}-${tag}`} className="rounded-full border border-white/10 px-3 py-1.5">
                        #{tag}
                      </span>
                    ))}
                  </div>
                </Link>

                <div className="flex items-center gap-3">
                  <button
                    type="button"
                    onClick={() => {
                      setEditingPaperId(paper.id);
                      setCategoryDraft(paper.category ?? "");
                      setTagsDraft((paper.tags ?? []).join(", "));
                    }}
                    className="rounded-full border border-white/10 px-4 py-2 text-xs text-mist"
                  >
                    整理
                  </button>
                  <button
                    type="button"
                    onClick={() =>
                      startTransition(async () => {
                        await deletePaper(paper.id);
                        router.refresh();
                      })
                    }
                    className="rounded-full border border-red-400/20 px-4 py-2 text-xs text-red-300"
                  >
                    删除
                  </button>
                </div>
              </div>

              {isEditing ? (
                <div className="mt-4 grid gap-3 rounded-3xl border border-white/10 bg-black/20 p-4 md:grid-cols-[1fr_1fr_auto]">
                  <input
                    value={categoryDraft}
                    onChange={(event) => setCategoryDraft(event.target.value)}
                    placeholder="分类，例如：CV / LLM / RAG"
                    className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white outline-none"
                  />
                  <input
                    value={tagsDraft}
                    onChange={(event) => setTagsDraft(event.target.value)}
                    placeholder="标签，逗号分隔"
                    className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white outline-none"
                  />
                  <div className="flex gap-2">
                    <button
                      type="button"
                      disabled={isPending}
                      onClick={() =>
                        startTransition(async () => {
                          await updatePaperMetadata(paper.id, {
                            category: categoryDraft || null,
                            tags: tagsDraft
                              .split(",")
                              .map((item) => item.trim())
                              .filter(Boolean),
                          });
                          setEditingPaperId(null);
                          router.refresh();
                        })
                      }
                      className="rounded-full bg-brand px-4 py-2 text-xs font-medium text-black disabled:opacity-50"
                    >
                      保存
                    </button>
                    <button
                      type="button"
                      onClick={() => setEditingPaperId(null)}
                      className="rounded-full border border-white/10 px-4 py-2 text-xs text-mist"
                    >
                      取消
                    </button>
                  </div>
                </div>
              ) : null}
            </div>
          );
        })
      )}
    </div>
  );
}
