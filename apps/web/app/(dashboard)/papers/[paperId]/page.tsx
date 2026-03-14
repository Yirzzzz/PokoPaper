import { AppShell } from "@/components/layout/app-shell";
import { ActivePaperSync } from "@/components/paper/active-paper-sync";
import { PaperWorkbench } from "@/components/paper/paper-workbench";
import { fetchOverview, fetchPapers } from "@/lib/api/client";
import {
  formatDexNumber,
  getCaptureStage,
  getPokemonCompanion,
  getPaperAffinity,
  getPaperTypeMeta,
} from "@/lib/pokedex";

export default async function PaperWorkbenchPage({
  params,
}: {
  params: Promise<{ paperId: string }>;
}) {
  const { paperId } = await params;
  const [overview, papers] = await Promise.all([
    fetchOverview(paperId),
    fetchPapers(),
  ]);
  const paper = papers.find((item) => item.id === paperId);
  const pokemon = paper ? getPokemonCompanion(paper) : null;
  const typeMeta = getPaperTypeMeta(paper?.category, paper?.tags);
  const captureStage = paper ? getCaptureStage(paper.status, paper.progress_percent) : "已收录";

  return (
    <AppShell
      citations={overview.main_experiments.map((item) => item.citation)}
      hints={overview.prerequisite_knowledge.map((item) => `${item.topic}: ${item.reason}`)}
      showContextPanel={false}
    >
      <ActivePaperSync paperId={paperId} />
      <div className="grid gap-4">
        <section className="pokedex-shell rounded-[2.5rem] border border-white/10 p-5 text-white">
          <div className="rounded-[2rem] border border-black/20 bg-black/15 p-5">
            <div className="flex items-center justify-between gap-3 text-[11px] uppercase tracking-[0.28em] text-white/80">
              <span>{pokemon ? formatDexNumber(pokemon.dexId - 1) : "No.???"}</span>
              <span>{pokemon?.name ?? ""}</span>
            </div>

            <div className="mt-4 grid gap-5 lg:grid-cols-[260px_minmax(0,1fr)]">
              <div className="pokedex-screen rounded-[1.75rem] border border-black/20 p-5">
                <p className="text-[11px] uppercase tracking-[0.28em] text-slate-600">伙伴</p>
                <h3 className="mt-2 text-2xl font-semibold text-slate-900">{pokemon?.name ?? ""}</h3>
                <div className="mt-4 grid place-items-center rounded-[1.5rem] border border-black/10 bg-white/40 py-6">
                  {pokemon ? (
                    <img
                      src={pokemon.spriteUrl}
                      alt={pokemon.name}
                      width={128}
                      height={128}
                      className="pixel-sprite h-32 w-32 object-contain"
                    />
                  ) : null}
                </div>
                <div className="mt-4 flex flex-wrap gap-2 text-xs">
                  <span className={`rounded-full border px-3 py-1.5 ${typeMeta.chipClassName}`}>
                    {typeMeta.label}
                  </span>
                  <span className="rounded-full border border-slate-400/30 bg-white/40 px-3 py-1.5 text-slate-700">
                    {captureStage}
                  </span>
                  <span className="rounded-full border border-slate-400/30 bg-white/40 px-3 py-1.5 text-slate-700">
                    属性 · {paper ? getPaperAffinity(paper) : "未设系别"}
                  </span>
                </div>
              </div>

              <div className="glass-panel p-6">
                <p className="text-xs uppercase tracking-[0.3em] text-brand">训练场</p>
                <h2 className="mt-3 text-3xl font-semibold text-slate-900">{paper?.title ?? "论文陪读"}</h2>
                <p className="mt-4 max-w-3xl text-sm leading-8 text-slate-700">{overview.tldr}</p>
                <div className="mt-5 flex flex-wrap gap-2">
                  <span className="rounded-full border border-black/10 bg-white/55 px-3 py-2 text-sm text-slate-700">
                    当前状态 {captureStage}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </section>
        <PaperWorkbench
          paperId={paperId}
          overview={overview}
        />
      </div>
    </AppShell>
  );
}
