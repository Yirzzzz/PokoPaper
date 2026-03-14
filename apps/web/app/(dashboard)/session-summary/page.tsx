import { AppShell } from "@/components/layout/app-shell";
import { SessionSummaryPanel } from "@/components/memory/session-summary-panel";
import { fetchSessionSummaries } from "@/lib/api/client";

export default async function SessionSummaryPage() {
  const response = await fetchSessionSummaries();

  return (
    <AppShell showContextPanel={false}>
      <SessionSummaryPanel initialItems={response.items} />
    </AppShell>
  );
}
