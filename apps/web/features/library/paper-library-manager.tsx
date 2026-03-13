"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMemo, useState, useTransition } from "react";
import { Pencil, Trash2 } from "lucide-react";

import { deletePaper, updatePaperMetadata } from "@/lib/api/client";
import {
  formatDexNumber,
  getCaptureStage,
  getPaperAffinity,
  getPaperTypeMeta,
  getPokemonCompanion,
} from "@/lib/pokedex";
import type { PaperCard } from "@/types";

type PaperLibraryManagerProps = {
  papers: PaperCard[];
  showPokedexControls?: boolean;
};

export function PaperLibraryManager({
  papers,
  showPokedexControls = false,
}: PaperLibraryManagerProps) {
  const router = useRouter();
  const [editingPaperId, setEditingPaperId] = useState<string | null>(null);
  const [categoryDraft, setCategoryDraft] = useState("");
  const [tagsDraft, setTagsDraft] = useState("");
  const [isPending, startTransition] = useTransition();
  const [statusFilter, setStatusFilter] = useState("全部状态");
  const [typeFilter, setTypeFilter] = useState("全部系别");
  const [sortMode, setSortMode] = useState("图鉴编号");

  const typeOptions = useMemo(() => {
    const values = new Set(
      papers.map((paper) => getPaperTypeMeta(paper.category, paper.tags).label),
    );
    return ["全部系别", ...Array.from(values)];
  }, [papers]);

  const statusOptions = ["全部状态", "待收服", "已收录", "训练中", "已掌握", "解析中"];
  const statusCounts = useMemo(
    () => ({
      全部状态: papers.length,
      待收服: papers.filter((paper) => getCaptureStage(paper.status, paper.progress_percent) === "待收服").length,
      已收录: papers.filter((paper) => getCaptureStage(paper.status, paper.progress_percent) === "已收录").length,
      训练中: papers.filter((paper) => getCaptureStage(paper.status, paper.progress_percent) === "训练中").length,
      已掌握: papers.filter((paper) => getCaptureStage(paper.status, paper.progress_percent) === "已掌握").length,
      解析中: papers.filter((paper) => getCaptureStage(paper.status, paper.progress_percent) === "解析中").length,
    }),
    [papers],
  );

  const visiblePapers = useMemo(() => {
    const filtered = papers.filter((paper) => {
      const typeLabel = getPaperTypeMeta(paper.category, paper.tags).label;
      const stage = getCaptureStage(paper.status, paper.progress_percent);
      const statusMatch = statusFilter === "全部状态" || stage === statusFilter;
      const typeMatch = typeFilter === "全部系别" || typeLabel === typeFilter;
      return statusMatch && typeMatch;
    });

    if (sortMode === "图鉴编号") {
      return [...filtered].sort((left, right) => {
        return getPokemonCompanion(left).dexId - getPokemonCompanion(right).dexId;
      });
    }

    if (sortMode === "训练进度") {
      return [...filtered].sort((left, right) => right.progress_percent - left.progress_percent);
    }

    return [...filtered].sort((left, right) => left.title.localeCompare(right.title));
  }, [papers, sortMode, statusFilter, typeFilter]);

  return (
    <div className="mt-5 space-y-5">
      {showPokedexControls ? (
        <section className="space-y-4 rounded-[2rem] border border-black/10 bg-white/55 p-4">
          <div className="grid gap-3 md:grid-cols-5">
            {statusOptions.map((item) => (
              <button
                key={item}
                type="button"
                onClick={() => setStatusFilter(item)}
                className={`rounded-[1.5rem] border px-4 py-4 text-left transition ${
                  statusFilter === item
                    ? "border-brand/50 bg-brand/20 shadow-[inset_0_1px_0_rgba(255,255,255,0.35)]"
                    : "border-black/10 bg-[#fffdf4]"
                }`}
              >
                <p
                  className={`text-[11px] uppercase tracking-[0.24em] ${
                    statusFilter === item ? "text-slate-800" : "text-slate-600"
                  }`}
                >
                  {item}
                </p>
                <p
                  className={`mt-2 text-2xl font-semibold ${
                    statusFilter === item ? "text-slate-950" : "text-slate-900"
                  }`}
                >
                  {statusCounts[item as keyof typeof statusCounts]}
                </p>
              </button>
            ))}
          </div>

          <div className="grid gap-3 md:grid-cols-3">
            <label className="grid gap-2 text-sm text-slate-700">
              <span>状态筛选</span>
              <select
                value={statusFilter}
                onChange={(event) => setStatusFilter(event.target.value)}
                className="rounded-2xl border border-black/10 bg-[#fffdf4] px-4 py-3 text-sm text-slate-900 outline-none"
              >
                {statusOptions.map((item) => (
                  <option key={item} value={item}>
                    {item}
                  </option>
                ))}
              </select>
            </label>
            <label className="grid gap-2 text-sm text-slate-700">
              <span>系别筛选</span>
              <select
                value={typeFilter}
                onChange={(event) => setTypeFilter(event.target.value)}
                className="rounded-2xl border border-black/10 bg-[#fffdf4] px-4 py-3 text-sm text-slate-900 outline-none"
              >
                {typeOptions.map((item) => (
                  <option key={item} value={item}>
                    {item}
                  </option>
                ))}
              </select>
            </label>
            <label className="grid gap-2 text-sm text-slate-700">
              <span>排序方式</span>
              <select
                value={sortMode}
                onChange={(event) => setSortMode(event.target.value)}
                className="rounded-2xl border border-black/10 bg-[#fffdf4] px-4 py-3 text-sm text-slate-900 outline-none"
              >
                {["图鉴编号", "训练进度", "论文标题"].map((item) => (
                  <option key={item} value={item}>
                    {item}
                  </option>
                ))}
              </select>
            </label>
          </div>
        </section>
      ) : null}

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4">
      {papers.length === 0 ? (
        <div className="w-full pokedex-shell rounded-[2.5rem] border border-white/10 p-5 text-white md:col-span-2 xl:col-span-3 2xl:col-span-4">
          <div className="pokedex-screen rounded-[2rem] border border-black/20 p-8 text-center">
            <p className="text-xs uppercase tracking-[0.3em] text-slate-700">Empty Slot</p>
            <h3 className="mt-3 text-2xl font-semibold text-slate-900">图鉴还没有收录论文</h3>
          </div>
        </div>
      ) : visiblePapers.length === 0 ? (
        <div className="w-full pokedex-shell rounded-[2.5rem] border border-white/10 p-5 text-white md:col-span-2 xl:col-span-3 2xl:col-span-4">
          <div className="pokedex-screen rounded-[2rem] border border-black/20 p-8 text-center">
            <p className="text-xs uppercase tracking-[0.3em] text-slate-700">Filtered Dex</p>
            <h3 className="mt-3 text-2xl font-semibold text-slate-900">当前筛选条件下没有论文</h3>
          </div>
        </div>
      ) : (
        visiblePapers.map((paper) => {
          const isEditing = editingPaperId === paper.id;
          const pokemon = getPokemonCompanion(paper);
          const typeMeta = getPaperTypeMeta(paper.category, paper.tags);
          const visibleTags = (paper.tags ?? []).filter((tag) => tag.trim() && tag.trim().toLowerCase() !== "unknown").slice(0, 2);
          const visibleAuthors = paper.authors
            .map((author) => author.trim())
            .filter((author) => author && author.toLowerCase() !== "unknown" && author.toLowerCase() !== "unknown author")
            .slice(0, 2);

          return (
            <article key={paper.id} className="pokedex-shell h-[372px] rounded-[2.5rem] border border-white/10 p-4 text-white">
              <div className="flex h-full flex-col rounded-[2rem] border border-black/20 bg-black/15 p-4">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-center gap-3 text-[11px] uppercase tracking-[0.28em] text-white/80">
                    <span>{formatDexNumber(pokemon.dexId - 1)}</span>
                    <span>{pokemon.name}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => {
                        setEditingPaperId(paper.id);
                        setCategoryDraft(paper.category ?? "");
                        setTagsDraft((paper.tags ?? []).join(", "));
                      }}
                      aria-label="调整属性"
                      title="调整属性"
                      className="grid h-8 w-8 place-items-center rounded-full border border-white/10 bg-white/10 text-white/90 transition hover:bg-white/15"
                    >
                      <Pencil className="h-3.5 w-3.5" />
                    </button>
                    <button
                      type="button"
                      onClick={() =>
                        startTransition(async () => {
                          await deletePaper(paper.id);
                          router.refresh();
                        })
                      }
                      aria-label="释放"
                      title="释放"
                      className="grid h-8 w-8 place-items-center rounded-full border border-red-200/30 text-red-100 transition hover:bg-red-200/10"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </div>
                </div>

                <Link href={`/papers/${paper.id}`} className="mt-4 block min-h-0 flex-1">
                  <div className="pokedex-screen flex h-full flex-col rounded-[1.75rem] border border-black/20 p-4">
                    <div className="grid flex-1 gap-3">
                      <div className="grid min-h-[116px] place-items-center rounded-[1.5rem] border border-black/10 bg-white/40 py-3">
                        <img
                          src={pokemon.spriteUrl}
                          alt={pokemon.name}
                          width={80}
                          height={80}
                          className="pixel-sprite h-20 w-20 object-contain"
                        />
                      </div>

                      <div className="min-w-0 space-y-2.5">
                        <div>
                          <p className="text-[11px] uppercase tracking-[0.28em] text-slate-600">论文</p>
                          <p className="mt-1.5 line-clamp-2 text-sm font-medium leading-5 text-slate-900">
                            {paper.title}
                          </p>
                        </div>

                        <div className="flex flex-wrap gap-1.5 text-xs">
                          <span className="rounded-full border border-slate-400/30 bg-white/40 px-3 py-1.5 text-slate-700">
                            {getCaptureStage(paper.status, paper.progress_percent)}
                          </span>
                          <span className="rounded-full border border-slate-400/30 bg-white/40 px-3 py-1.5 text-slate-700">
                            属性 · {getPaperAffinity(paper)}
                          </span>
                          {visibleTags.map((tag) => (
                            <span
                              key={`${paper.id}-${tag}`}
                              className="rounded-full border border-slate-400/30 bg-white/40 px-3 py-1.5 text-slate-700"
                            >
                              {tag}
                            </span>
                          ))}
                        </div>

                        {visibleAuthors.length > 0 ? (
                          <p className="line-clamp-1 text-xs text-slate-600">
                            {visibleAuthors.join(", ")}
                          </p>
                        ) : null}
                      </div>
                    </div>
                  </div>
                </Link>
              </div>

              {isEditing ? (
                <div className="mt-4 grid gap-3 rounded-[1.75rem] border border-white/10 bg-black/20 p-4 md:grid-cols-[1fr_1fr_auto]">
                  <input
                    value={categoryDraft}
                    onChange={(event) => setCategoryDraft(event.target.value)}
                    placeholder="系别，例如：CV / LLM / RAG"
                    className="rounded-2xl border border-white/10 bg-white/20 px-4 py-3 text-sm text-white outline-none placeholder:text-white/60"
                  />
                  <input
                    value={tagsDraft}
                    onChange={(event) => setTagsDraft(event.target.value)}
                    placeholder="属性标签，逗号分隔"
                    className="rounded-2xl border border-white/10 bg-white/20 px-4 py-3 text-sm text-white outline-none placeholder:text-white/60"
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
                      className="rounded-full border border-white/10 px-4 py-2 text-xs text-white/80"
                    >
                      取消
                    </button>
                  </div>
                </div>
              ) : null}
            </article>
          );
        })
      )}
      </div>
    </div>
  );
}
