import { AppShell } from "@/components/layout/app-shell";
import { PaperWorkbench } from "@/components/paper/paper-workbench";
import { fetchMemoryOverview, fetchOverview, fetchPaperMemory } from "@/lib/api/client";

export default async function PaperWorkbenchPage({
  params,
}: {
  params: Promise<{ paperId: string }>;
}) {
  const { paperId } = await params;
  const [overview, paperMemory, memoryOverview] = await Promise.all([
    fetchOverview(paperId),
    fetchPaperMemory(paperId),
    fetchMemoryOverview(),
  ]);

  return (
    <AppShell
      citations={overview.main_experiments.map((item) => item.citation)}
      hints={overview.prerequisite_knowledge.map((item) => `${item.topic}: ${item.reason}`)}
      showContextPanel={false}
    >
      <div className="grid gap-4">
        <section className="glass-panel p-8">
          <p className="text-xs uppercase tracking-[0.3em] text-brand">论文页</p>
          <h2 className="mt-3 text-3xl font-semibold text-white">论文陪读</h2>
          <p className="mt-4 max-w-3xl text-sm leading-8 text-mist">{overview.tldr}</p>
          <div className="mt-5 flex flex-wrap gap-2">
            <span className="rounded-full border border-white/10 px-3 py-2 text-sm text-mist">
              阅读进度 {paperMemory.progress_percent}%
            </span>
            <span className="rounded-full border border-white/10 px-3 py-2 text-sm text-mist">
              上次读到 {paperMemory.last_read_section}
            </span>
          </div>
        </section>
        <PaperWorkbench
          paperId={paperId}
          overview={overview}
          paperMemory={paperMemory}
          memoryOverview={memoryOverview}
        />
      </div>
    </AppShell>
  );
}
