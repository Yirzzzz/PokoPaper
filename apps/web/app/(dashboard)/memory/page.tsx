import { AppShell } from "@/components/layout/app-shell";
import { MemoryPanel } from "@/components/memory/memory-panel";
import { fetchMemoryOverview, fetchPaperMemory, fetchPapers } from "@/lib/api/client";

export default async function MemoryPage() {
  const [overview, papers] = await Promise.all([fetchMemoryOverview(), fetchPapers()]);
  const paper = papers[0];
  const paperMemory = paper ? await fetchPaperMemory(paper.id) : null;

  return (
    <AppShell showContextPanel={false}>
      {paperMemory ? (
        <MemoryPanel overview={overview} paperMemory={paperMemory} />
      ) : (
        <section className="glass-panel p-6 text-sm text-slate-700">
          还没有记录。
        </section>
      )}
    </AppShell>
  );
}
