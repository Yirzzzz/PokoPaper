import { AppShell } from "@/components/layout/app-shell";
import { ChatPanel } from "@/components/chat/chat-panel";
import { fetchPapers } from "@/lib/api/client";

export default async function ChatPage() {
  const papers = await fetchPapers();
  const paper = papers[0];
  return (
    <AppShell>
      {paper ? (
        <ChatPanel paperId={paper.id} />
      ) : (
        <section className="glass-panel p-6 text-sm text-mist">
          还没有可聊天的论文。请先在首页上传 PDF。
        </section>
      )}
    </AppShell>
  );
}
