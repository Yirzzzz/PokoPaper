import { AppShell } from "@/components/layout/app-shell";
import { MainChatPanel } from "@/components/chat/main-chat-panel";

export default function ChatPage() {
  return (
    <AppShell showContextPanel={false}>
      <MainChatPanel />
    </AppShell>
  );
}
