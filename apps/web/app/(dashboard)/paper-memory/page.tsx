import { AppShell } from "@/components/layout/app-shell";
import { PaperEntityMemoryPanel } from "@/components/memory/paper-entity-memory-panel";
import { fetchPaperEntityMemories } from "@/lib/api/client";

export default async function PaperMemoryPage() {
  const response = await fetchPaperEntityMemories();

  return (
    <AppShell showContextPanel={false}>
      <PaperEntityMemoryPanel initialItems={response.items} />
    </AppShell>
  );
}
