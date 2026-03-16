import { AppShell } from "@/components/layout/app-shell";
import { MemoryCenter } from "@/components/memory/memory-center";
import {
  fetchPaperEntityMemories,
  fetchPapers,
  fetchSessionMemories,
  fetchSessionSummaries,
  fetchUserEntityMemory,
} from "@/lib/api/client";

export default async function MemoryPage() {
  const [memory, papers, instantMemories, summaries, paperMemories] = await Promise.allSettled([
    fetchUserEntityMemory(),
    fetchPapers(),
    fetchSessionMemories(),
    fetchSessionSummaries(),
    fetchPaperEntityMemories(),
  ]);

  if (memory.status !== "fulfilled") {
    throw memory.reason;
  }
  if (papers.status !== "fulfilled") {
    throw papers.reason;
  }
  if (instantMemories.status !== "fulfilled") {
    throw instantMemories.reason;
  }
  if (summaries.status !== "fulfilled") {
    throw summaries.reason;
  }

  const paperMemoryItems = paperMemories.status === "fulfilled" ? paperMemories.value.items : [];

  return (
    <AppShell showContextPanel={false}>
      <MemoryCenter
        instantMemoryItems={instantMemories.value.items}
        summaryItems={summaries.value.items}
        userMemory={memory.value}
        papers={papers.value}
        paperMemoryItems={paperMemoryItems}
      />
    </AppShell>
  );
}
