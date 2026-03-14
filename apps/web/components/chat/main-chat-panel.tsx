"use client";

import { useEffect, useMemo, useState, useTransition } from "react";

import {
  createGlobalConversation,
  deleteGlobalConversation,
  fetchGlobalConversations,
} from "@/lib/api/client";
import { useAppStore } from "@/store/app-store";
import { ChatPanel } from "@/components/chat/chat-panel";

export function MainChatPanel() {
  const [loading, setLoading] = useState(true);
  const [isPending, startTransition] = useTransition();
  const {
    activeGlobalConversationId,
    globalConversations,
    setActiveGlobalConversationId,
    setGlobalConversations,
    upsertGlobalConversation,
    removeGlobalConversation,
  } = useAppStore();

  useEffect(() => {
    let alive = true;
    void fetchGlobalConversations()
      .then(async ({ conversations }) => {
        if (!alive) return;
        if (conversations.length === 0) {
          const created = await createGlobalConversation();
          if (!alive) return;
          setGlobalConversations([created]);
          setActiveGlobalConversationId(created.conversation_id);
          return;
        }
        setGlobalConversations(conversations);
        const nextActive = conversations.some(
          (item) => item.conversation_id === activeGlobalConversationId,
        )
          ? activeGlobalConversationId
          : conversations[0].conversation_id;
        setActiveGlobalConversationId(nextActive);
      })
      .finally(() => {
        if (alive) setLoading(false);
      });
    return () => {
      alive = false;
    };
  }, [
    activeGlobalConversationId,
    setActiveGlobalConversationId,
    setGlobalConversations,
  ]);

  const activeConversation = useMemo(
    () =>
      globalConversations.find((item) => item.conversation_id === activeGlobalConversationId)
      ?? globalConversations[0]
      ?? null,
    [activeGlobalConversationId, globalConversations],
  );

  const handleCreateConversation = () =>
    startTransition(async () => {
      const created = await createGlobalConversation(
        `Global Chat ${globalConversations.length + 1}`,
      );
      upsertGlobalConversation(created);
      setActiveGlobalConversationId(created.conversation_id);
    });

  const handleDeleteConversation = (conversationId: string) =>
    startTransition(async () => {
      await deleteGlobalConversation(conversationId);
      removeGlobalConversation(conversationId);
    });

  if (loading) {
    return (
      <section className="glass-panel flex min-h-[560px] items-center justify-center p-8">
        <p className="text-sm text-slate-700">正在载入对话…</p>
      </section>
    );
  }

  if (!activeConversation) {
    return (
      <section className="glass-panel flex min-h-[560px] items-center justify-center p-8">
        <button
          type="button"
          onClick={handleCreateConversation}
          className="rounded-full bg-brand px-5 py-3 text-sm font-medium text-slate-900"
        >
          新建全局会话
        </button>
      </section>
    );
  }

  return (
    <div className="grid gap-4 xl:grid-cols-[280px_minmax(0,1fr)]">
      <aside className="glass-panel flex min-h-[560px] flex-col gap-4 p-4">
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="text-xs uppercase tracking-[0.24em] text-brand">对战记录</p>
            <h2 className="mt-2 text-lg font-semibold text-slate-900">Global Chats</h2>
          </div>
          <button
            type="button"
            onClick={handleCreateConversation}
            className="rounded-full border border-black/10 bg-white/70 px-4 py-2 text-sm text-slate-900"
          >
            新建
          </button>
        </div>
        <div className="space-y-2 overflow-y-auto">
          {globalConversations.map((conversation) => {
            const selected = conversation.conversation_id === activeConversation.conversation_id;
            return (
              <div
                key={conversation.conversation_id}
                className={`rounded-3xl border px-4 py-3 ${
                  selected ? "border-brand/40 bg-brand/10" : "border-black/10 bg-white/55"
                }`}
              >
                <button
                  type="button"
                  onClick={() => setActiveGlobalConversationId(conversation.conversation_id)}
                  className="w-full text-left"
                >
                  <p className="text-sm font-medium text-slate-900">{conversation.title}</p>
                  <p className="mt-1 text-xs text-slate-600">{conversation.updated_at}</p>
                </button>
                <button
                  type="button"
                  onClick={() => handleDeleteConversation(conversation.conversation_id)}
                  disabled={isPending}
                  className="mt-3 text-xs text-rose-600"
                >
                  删除
                </button>
              </div>
            );
          })}
        </div>
      </aside>
      <ChatPanel
        chatKey={activeConversation.conversation_id}
        conversationId={activeConversation.conversation_id}
        conversationType="global_chat"
      />
    </div>
  );
}
