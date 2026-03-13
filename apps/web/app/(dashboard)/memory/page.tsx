import { AppShell } from "@/components/layout/app-shell";
import { MemoryPanel } from "@/components/memory/memory-panel";
import { fetchMemoryOverview, fetchPaperMemory, fetchPapers } from "@/lib/api/client";

export default async function MemoryPage() {
  const [overview, papers] = await Promise.all([fetchMemoryOverview(), fetchPapers()]);
  const paper = papers[0];
  const paperMemory = paper ? await fetchPaperMemory(paper.id) : null;

  return (
    <AppShell>
      {paperMemory ? (
        <MemoryPanel overview={overview} paperMemory={paperMemory} />
      ) : (
        <section className="glass-panel p-6 text-sm text-mist">
          还没有阅读记忆。上传并阅读第一篇论文后，这里会出现你的进度、卡点和学习路径。
        </section>
      )}
    </AppShell>
  );
}
