import { AppShell } from "@/components/layout/app-shell";
import { SessionMemoryPanel } from "@/components/memory/session-memory-panel";
import { fetchSessionMemories } from "@/lib/api/client";

export default async function SessionMemoryPage() {
  const response = await fetchSessionMemories();

  return (
    <AppShell showContextPanel={false}>
      <SessionMemoryPanel initialItems={response.items} />
    </AppShell>
  );
}
