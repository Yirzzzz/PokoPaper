import { AppShell } from "@/components/layout/app-shell";
import { LongTermMemoryPanel } from "@/components/memory/long-term-memory-panel";
import { fetchLongTermMemories } from "@/lib/api/client";

export default async function LongTermMemoryPage() {
  const memories = await fetchLongTermMemories();

  return (
    <AppShell showContextPanel={false}>
      <LongTermMemoryPanel initialItems={memories.items} />
    </AppShell>
  );
}
