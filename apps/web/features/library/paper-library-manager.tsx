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

  const statusOptions = ["全部状态", "待收服", "已收录", "训练中", "已掌握"];
  const statusCounts = useMemo(
    () => ({
      全部状态: papers.length,
      待收服: papers.filter((paper) => getCaptureStage(paper.status, paper.progress_percent) === "待收服").length,
      已收录: papers.filter((paper) => getCaptureStage(paper.status, paper.progress_percent) === "已收录").length,
      训练中: papers.filter((paper) => getCaptureStage(paper.status, paper.progress_percent) === "训练中").length,
      已掌握: papers.filter((paper) => getCaptureStage(paper.status, paper.progress_percent) === "已掌握").length,
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

  const editingPaper = editingPaperId
    ? papers.find((paper) => paper.id === editingPaperId) ?? null
    : null;

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
          const visibleTags = (paper.tags ?? []).filter((tag) => tag.trim() && tag.trim().toLowerCase() !== "unknown").slice(0, 1);

          return (
            <article key={paper.id} className="pokedex-shell h-[372px] rounded-[2.5rem] border border-white/10 p-4 text-white">
              <div className="flex h-full flex-col rounded-[2rem] border border-black/20 bg-black/15 p-4">
                <div className="flex items-start justify-between gap-2.5">
                  <div className="min-w-0 flex-1 space-y-2">
                    <div className="flex items-center gap-3 text-[11px] uppercase tracking-[0.28em] text-white/80">
                      <span>{formatDexNumber(pokemon.dexId - 1)}</span>
                      <span>{pokemon.name}</span>
                    </div>
                    <div className="flex flex-wrap items-center gap-1.5 text-[11px]">
                      <span className="whitespace-nowrap rounded-full border border-white/10 bg-white/10 px-2 py-1 text-white/85">
                        {getCaptureStage(paper.status, paper.progress_percent)}
                      </span>
                      <span className="whitespace-nowrap rounded-full border border-white/10 bg-white/10 px-2 py-1 text-white/85">
                        属性 · {getPaperAffinity(paper)}
                      </span>
                    </div>
                    {visibleTags.length > 0 ? (
                      <div className="flex max-h-[22px] flex-wrap gap-1.5 overflow-hidden text-[11px]">
                        {visibleTags.map((tag) => (
                          <span
                            key={`${paper.id}-${tag}`}
                            className="rounded-full border border-white/10 bg-white/10 px-2 py-1 text-white/85"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    ) : null}
                  </div>
                  <div className="flex items-center gap-1.5">
                    <button
                      type="button"
                      onClick={() => {
                        setEditingPaperId(paper.id);
                        setCategoryDraft(paper.category ?? "");
                        setTagsDraft((paper.tags ?? []).join(", "));
                      }}
                      aria-label="调整属性"
                      title="调整属性"
                      className="grid h-7 w-7 place-items-center rounded-full border border-white/10 bg-white/10 text-white/90 transition hover:bg-white/15"
                    >
                      <Pencil className="h-3 w-3" />
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
                      className="grid h-7 w-7 place-items-center rounded-full border border-red-200/30 text-red-100 transition hover:bg-red-200/10"
                    >
                      <Trash2 className="h-3 w-3" />
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
                          <p className="mt-1.5 line-clamp-3 min-h-[4.2rem] text-[13px] font-medium leading-5 text-slate-900">
                            {paper.title}
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                </Link>
              </div>

            </article>
          );
        })
      )}
      </div>

      {editingPaper ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/45 p-4 backdrop-blur-sm">
          <div className="w-full max-w-2xl rounded-[2rem] border border-black/10 bg-[linear-gradient(180deg,rgba(255,252,240,0.98),rgba(247,241,221,0.98))] p-6 shadow-[0_24px_120px_rgba(15,23,42,0.28)]">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-xs uppercase tracking-[0.28em] text-brand">编辑图鉴属性</p>
                <h3 className="mt-3 text-2xl font-semibold text-slate-900">{editingPaper.title}</h3>
                <p className="mt-2 text-sm text-slate-700">调整论文的系别与标签，不打断当前图鉴卡片的展示。</p>
              </div>
              <button
                type="button"
                onClick={() => setEditingPaperId(null)}
                className="rounded-full border border-black/10 bg-white/70 px-4 py-2 text-sm text-slate-700"
              >
                关闭
              </button>
            </div>

            <div className="mt-6 grid gap-4">
              <label className="grid gap-2 text-sm text-slate-700">
                <span>系别 / Category</span>
                <input
                  value={categoryDraft}
                  onChange={(event) => setCategoryDraft(event.target.value)}
                  placeholder="例如：CV / LLM / RAG / Agents"
                  className="rounded-[1.25rem] border border-black/10 bg-white/80 px-4 py-3 text-sm text-slate-900 outline-none placeholder:text-slate-500"
                />
              </label>

              <label className="grid gap-2 text-sm text-slate-700">
                <span>属性标签 / Tags</span>
                <input
                  value={tagsDraft}
                  onChange={(event) => setTagsDraft(event.target.value)}
                  placeholder="逗号分隔，例如：retrieval, planning, multimodal"
                  className="rounded-[1.25rem] border border-black/10 bg-white/80 px-4 py-3 text-sm text-slate-900 outline-none placeholder:text-slate-500"
                />
              </label>

              <div className="rounded-[1.5rem] border border-black/10 bg-white/60 p-4">
                <p className="text-xs uppercase tracking-[0.24em] text-slate-500">预览</p>
                <div className="mt-3 flex flex-wrap gap-2 text-sm">
                  <span className="rounded-full border border-black/10 bg-white/85 px-3 py-2 text-slate-800">
                    系别 · {categoryDraft.trim() || "未设系别"}
                  </span>
                  {tagsDraft
                    .split(",")
                    .map((item) => item.trim())
                    .filter(Boolean)
                    .slice(0, 4)
                    .map((tag) => (
                      <span
                        key={`${editingPaper.id}-${tag}`}
                        className="rounded-full border border-black/10 bg-white/85 px-3 py-2 text-slate-700"
                      >
                        {tag}
                      </span>
                    ))}
                </div>
              </div>

              <div className="flex flex-col gap-3 pt-2 sm:flex-row sm:justify-end">
                <button
                  type="button"
                  onClick={() => setEditingPaperId(null)}
                  className="rounded-full border border-black/10 bg-white/70 px-5 py-3 text-sm text-slate-700"
                >
                  取消
                </button>
                <button
                  type="button"
                  disabled={isPending}
                  onClick={() =>
                    startTransition(async () => {
                      await updatePaperMetadata(editingPaper.id, {
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
                  className="rounded-full bg-brand px-5 py-3 text-sm font-medium text-slate-900 disabled:opacity-50"
                >
                  保存修改
                </button>
              </div>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
