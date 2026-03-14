import { AppShell } from "@/components/layout/app-shell";
import { ChatPanel } from "@/components/chat/chat-panel";
import { fetchPapers } from "@/lib/api/client";

export default async function ChatPage() {
  const papers = await fetchPapers();
  const paper = papers[0];
  return (
    <AppShell showContextPanel={false}>
      {paper ? (
        <ChatPanel paperId={paper.id} />
      ) : (
        <section className="glass-panel p-6 text-sm text-slate-700">
          先收录一篇论文。
        </section>
      )}
    </AppShell>
  );
}
