"use client";

import { useEffect, useRef, useState, useTransition } from "react";
import ReactMarkdown from "react-markdown";
import rehypeKatex from "rehype-katex";
import remarkMath from "remark-math";

import {
  askQuestion,
  fetchChatMessages,
  fetchChatModels,
  getOrCreatePaperConversation,
} from "@/lib/api/client";
import { useAppStore } from "@/store/app-store";
import type { ChatHistoryMessage, ChatModelOption } from "@/types";

type ChatPanelProps = {
  paperId?: string | null;
  initialQuestion?: string;
  chatKey: string;
  conversationId?: string | null;
  conversationType?: "paper_chat" | "global_chat";
};

export function ChatPanel({
  paperId,
  initialQuestion,
  chatKey,
  conversationId,
  conversationType = "paper_chat",
}: ChatPanelProps) {
  const [models, setModels] = useState<ChatModelOption[]>([]);
  const [isPending, startTransition] = useTransition();
  const messagesContainerRef = useRef<HTMLDivElement | null>(null);
  const bottomAnchorRef = useRef<HTMLDivElement | null>(null);
  const resolvedInitialQuestion =
    initialQuestion ?? (conversationType === "global_chat" ? "" : "这篇论文主要做了什么？");
  const {
    initializeChatState,
    chatStates,
    setConversationId,
    hydrateChatHistory,
    setDraftQuestion,
    setSelectedModel,
    setEnableThinking,
    appendChatTurn,
  } = useAppStore();
  const chatState = chatStates[chatKey] ?? {
    conversationId: null,
    draftQuestion: resolvedInitialQuestion,
    selectedModel: "",
    enableThinking: false,
    turns: [],
    historyLoaded: false,
    historyMessages: [],
  };

  useEffect(() => {
    initializeChatState(chatKey, resolvedInitialQuestion);
  }, [chatKey, initializeChatState, resolvedInitialQuestion]);

  useEffect(() => {
    const container = messagesContainerRef.current;
    if (!container) return;
    container.scrollTop = container.scrollHeight;
    bottomAnchorRef.current?.scrollIntoView({ block: "end" });
  }, [chatState.historyMessages.length, chatState.turns.length, chatKey]);

  useEffect(() => {
    let active = true;
    const conversationPromise =
      conversationType === "paper_chat" && paperId ? getOrCreatePaperConversation(paperId) : Promise.resolve(null);
    void Promise.all([fetchChatModels(), conversationPromise]).then(async ([items, conversation]) => {
      if (!active) return;
      const enabled = items.filter((item) => item.enabled);
      setModels(enabled);
      if (!chatState.selectedModel) {
        setSelectedModel(chatKey, enabled[0]?.id ?? "");
      }
      const resolvedConversationId = conversationId ?? conversation?.conversation_id ?? null;
      if (!resolvedConversationId) {
        return;
      }
      setConversationId(chatKey, resolvedConversationId);
      if (!chatState.historyLoaded || chatState.conversationId !== resolvedConversationId) {
        const messages = await fetchChatMessages(resolvedConversationId);
        if (!active) return;
        hydrateChatHistory(chatKey, messages);
      }
    });
    return () => {
      active = false;
    };
  }, [
    chatKey,
    chatState.historyLoaded,
    chatState.conversationId,
    conversationType,
    conversationId,
    hydrateChatHistory,
    paperId,
    setConversationId,
    setSelectedModel,
    chatState.selectedModel,
  ]);

  return (
    <section className="glass-panel flex min-h-[calc(100dvh-12rem)] flex-col overflow-hidden p-0 sm:min-h-[calc(100dvh-11rem)] xl:h-[calc(100dvh-8rem)] xl:min-h-[720px]">
      <div className="flex shrink-0 flex-col gap-4 border-b border-black/10 px-4 py-4 md:px-6 md:py-5 xl:flex-row xl:items-start xl:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.24em] text-brand">对战记录</p>
          <h3 className="mt-2 text-xl font-semibold text-slate-900">对话</h3>
        </div>
        <div className="w-full xl:min-w-72 xl:max-w-80">
          <label className="mb-2 block text-xs uppercase tracking-[0.24em] text-slate-700">可选模型</label>
          <select
            value={chatState.selectedModel}
            onChange={(event) => setSelectedModel(chatKey, event.target.value)}
            className="w-full rounded-2xl border border-black/10 bg-white/70 px-4 py-3 text-sm text-slate-900 outline-none"
          >
            {models.length === 0 ? <option value="">当前没有可用模型</option> : null}
            {models.map((model) => (
              <option key={model.id} value={model.id}>
                {model.label}
              </option>
            ))}
          </select>
          <label className="mt-3 flex items-center gap-2 text-xs text-slate-700">
            <input
              type="checkbox"
              checked={chatState.enableThinking}
              onChange={(event) => setEnableThinking(chatKey, event.target.checked)}
              className="h-4 w-4 rounded border-black/20 bg-white/70"
            />
            开启 thinking 模式
          </label>
        </div>
      </div>

      <div ref={messagesContainerRef} className="min-h-0 flex-1 overflow-y-auto px-4 py-4 md:px-6 md:py-5">
        {chatState.historyMessages.length > 0 || chatState.turns.length > 0 ? (
          <div className="space-y-5">
          {chatState.historyMessages.map((message: ChatHistoryMessage, index) => (
            <div key={`${message.message_id}-${message.created_at}-${index}`} className="space-y-3">
              {message.role === "user" ? (
                <div className="ml-auto max-w-full rounded-[24px] rounded-br-lg border border-emerald-200 bg-emerald-100/90 px-4 py-3 text-sm leading-7 text-slate-900 shadow-glow sm:max-w-[88%] md:max-w-[85%] md:px-5 md:py-4">
                  {message.content_md}
                </div>
              ) : (
                <div className="max-w-full rounded-[24px] rounded-bl-lg border border-black/10 bg-[#fffdf4]/90 px-4 py-4 sm:max-w-[96%] md:max-w-[92%] md:px-5 md:py-5">
                  <div className="chat-markdown">
                    <ReactMarkdown remarkPlugins={[remarkMath]} rehypePlugins={[rehypeKatex]}>
                      {message.content_md}
                    </ReactMarkdown>
                  </div>
                </div>
              )}
            </div>
          ))}
          {chatState.turns.map((turn) => {
            const response = turn.response;
            return (
              <div key={turn.id} className="space-y-5">
                <div className="ml-auto max-w-full rounded-[24px] rounded-br-lg border border-emerald-200 bg-emerald-100/90 px-4 py-3 text-sm leading-7 text-slate-900 shadow-glow sm:max-w-[88%] md:max-w-[85%] md:px-5 md:py-4">
                  {turn.question}
                </div>
                <div className="max-w-full rounded-[24px] rounded-bl-lg border border-black/10 bg-[#fffdf4]/90 px-4 py-4 sm:max-w-[96%] md:max-w-[92%] md:px-5 md:py-5">
                  <div className="chat-markdown">
                    <ReactMarkdown remarkPlugins={[remarkMath]} rehypePlugins={[rehypeKatex]}>
                      {response.answer_md}
                    </ReactMarkdown>
                  </div>
                </div>
                {response.citations.length > 0 ? (
                  <div className="max-w-full rounded-3xl border border-black/10 bg-white/55 p-4 sm:max-w-[96%] md:max-w-[92%]">
                    <p className="text-xs uppercase tracking-[0.24em] text-brand">引用来源</p>
                    <div className="mt-3 flex flex-wrap gap-2">
                      {response.citations.map((citation, index) => (
                        <span
                          key={`${turn.id}-${citation.chunk_id}-${index}`}
                          className="rounded-full border border-black/10 bg-white/65 px-3 py-2 text-xs text-slate-700"
                        >
                          {citation.section_title} · p.{citation.page_num}
                        </span>
                      ))}
                    </div>
                  </div>
                ) : null}
                {response.suggested_followups.length > 0 ? (
                  <div className="max-w-full rounded-3xl border border-black/10 bg-white/55 p-4 sm:max-w-[96%] md:max-w-[92%]">
                    <p className="text-xs uppercase tracking-[0.24em] text-brand">猜你想问</p>
                    <div className="mt-3 flex flex-wrap gap-2">
                      {response.suggested_followups.map((item) => (
                        <button
                          key={`${turn.id}-${item}`}
                          type="button"
                          onClick={() => setDraftQuestion(chatKey, item)}
                          className="rounded-full border border-black/10 bg-white/65 px-3 py-2 text-xs text-slate-700"
                        >
                          {item}
                        </button>
                      ))}
                    </div>
                  </div>
                ) : null}
              </div>
            );
          })}
          <div ref={bottomAnchorRef} />
          </div>
        ) : (
          <div className="flex h-full items-center justify-center">
            <div className="max-w-xl text-center">
              <p className="text-sm text-slate-700">提问。</p>
            </div>
          </div>
        )}
      </div>

      <div className="shrink-0 border-t border-black/10 bg-white/35 px-4 py-4 backdrop-blur-xl md:px-6">
        <div className="rounded-[24px] border border-black/10 bg-white/70 p-3 md:rounded-[28px]">
          <textarea
            value={chatState.draftQuestion}
            onChange={(event) => setDraftQuestion(chatKey, event.target.value)}
            className="h-24 max-h-40 w-full resize-y bg-transparent p-2 text-sm text-slate-900 outline-none md:h-28"
            placeholder="输入你的问题..."
          />
          <div className="mt-3 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-end">
            <button
              type="button"
              onClick={() =>
                startTransition(async () => {
                  const result = await askQuestion(
                    paperId,
                    chatState.draftQuestion,
                    chatState.selectedModel || undefined,
                    chatState.enableThinking,
                    chatState.conversationId ?? undefined,
                  );
                  appendChatTurn(chatKey, {
                    id: `${result.message_id}-${Date.now()}`,
                    question: chatState.draftQuestion,
                    response: result,
                  });
                })
              }
              className="w-full rounded-full bg-brand px-5 py-3 text-sm font-medium text-slate-900 sm:w-auto"
            >
              {isPending ? "思考中..." : "发送"}
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}
