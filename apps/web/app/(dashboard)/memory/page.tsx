import { AppShell } from "@/components/layout/app-shell";
import { EntityMemoryPanel } from "@/components/memory/entity-memory-panel";
import { fetchPapers, fetchUserEntityMemory } from "@/lib/api/client";

export default async function MemoryPage() {
  const [memory, papers] = await Promise.all([
    fetchUserEntityMemory(),
    fetchPapers(),
  ]);

  return (
    <AppShell showContextPanel={false}>
      <EntityMemoryPanel initialMemory={memory} initialPapers={papers} />
    </AppShell>
  );
}
