"use client";

import { useEffect, useState, useTransition } from "react";
import ReactMarkdown from "react-markdown";
import rehypeKatex from "rehype-katex";
import remarkMath from "remark-math";

import {
  askQuestion,
  fetchChatMessages,
  fetchChatModels,
  getOrCreateChatSession,
} from "@/lib/api/client";
import { useAppStore } from "@/store/app-store";
import type { ChatHistoryMessage, ChatModelOption } from "@/types";

type ChatPanelProps = {
  paperId: string;
  initialQuestion?: string;
};

export function ChatPanel({ paperId, initialQuestion = "这篇论文主要做了什么？" }: ChatPanelProps) {
  const [models, setModels] = useState<ChatModelOption[]>([]);
  const [isPending, startTransition] = useTransition();
  const {
    initializePaperChat,
    paperChats,
    setSessionId,
    hydrateChatHistory,
    setDraftQuestion,
    setSelectedModel,
    setEnableThinking,
    appendChatTurn,
  } = useAppStore();
  const chatState = paperChats[paperId] ?? {
    sessionId: null,
    draftQuestion: initialQuestion,
    selectedModel: "",
    enableThinking: false,
    turns: [],
    historyLoaded: false,
    historyMessages: [],
  };

  useEffect(() => {
    initializePaperChat(paperId, initialQuestion);
  }, [initializePaperChat, initialQuestion, paperId]);

  useEffect(() => {
    let active = true;
    void Promise.all([fetchChatModels(), getOrCreateChatSession(paperId)]).then(async ([items, session]) => {
      if (!active) return;
      const enabled = items.filter((item) => item.enabled);
      setModels(enabled);
      if (!chatState.selectedModel) {
        setSelectedModel(paperId, enabled[0]?.id ?? "");
      }
      setSessionId(paperId, session.session_id);
      if (!chatState.historyLoaded) {
        const messages = await fetchChatMessages(session.session_id);
        if (!active) return;
        hydrateChatHistory(paperId, messages);
      }
    });
    return () => {
      active = false;
    };
  }, [chatState.historyLoaded, chatState.selectedModel, hydrateChatHistory, paperId, setSelectedModel, setSessionId]);

  return (
    <section className="glass-panel flex min-h-[calc(100dvh-12rem)] flex-col overflow-hidden p-0 sm:min-h-[calc(100dvh-11rem)] xl:h-[calc(100dvh-8rem)] xl:min-h-[720px]">
      <div className="flex shrink-0 flex-col gap-4 border-b border-white/10 px-4 py-4 md:px-6 md:py-5 xl:flex-row xl:items-start xl:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.24em] text-brand">问答</p>
          <h3 className="mt-2 text-xl font-semibold text-white">对话</h3>
        </div>
        <div className="w-full xl:min-w-72 xl:max-w-80">
          <label className="mb-2 block text-xs uppercase tracking-[0.24em] text-mist">可选模型</label>
          <select
            value={chatState.selectedModel}
            onChange={(event) => setSelectedModel(paperId, event.target.value)}
            className="w-full rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-sm text-white outline-none"
          >
            {models.length === 0 ? <option value="">当前没有可用模型</option> : null}
            {models.map((model) => (
              <option key={model.id} value={model.id}>
                {model.label}
              </option>
            ))}
          </select>
          <label className="mt-3 flex items-center gap-2 text-xs text-mist">
            <input
              type="checkbox"
              checked={chatState.enableThinking}
              onChange={(event) => setEnableThinking(paperId, event.target.checked)}
              className="h-4 w-4 rounded border-white/20 bg-black/20"
            />
            开启 thinking 模式
          </label>
        </div>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto px-4 py-4 md:px-6 md:py-5">
        {chatState.historyMessages.length > 0 || chatState.turns.length > 0 ? (
          <div className="space-y-5">
          {chatState.historyMessages.map((message: ChatHistoryMessage, index) => (
            <div key={`${message.message_id}-${message.created_at}-${index}`} className="space-y-3">
              {message.role === "user" ? (
                <div className="ml-auto max-w-full rounded-[24px] rounded-br-lg bg-brand px-4 py-3 text-sm leading-7 text-black shadow-glow sm:max-w-[88%] md:max-w-[85%] md:px-5 md:py-4">
                  {message.content_md}
                </div>
              ) : (
                <div className="max-w-full rounded-[24px] rounded-bl-lg border border-white/10 bg-white/5 px-4 py-4 sm:max-w-[96%] md:max-w-[92%] md:px-5 md:py-5">
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
                <div className="ml-auto max-w-full rounded-[24px] rounded-br-lg bg-brand px-4 py-3 text-sm leading-7 text-black shadow-glow sm:max-w-[88%] md:max-w-[85%] md:px-5 md:py-4">
                  {turn.question}
                </div>
                <div className="max-w-full rounded-[24px] rounded-bl-lg border border-white/10 bg-white/5 px-4 py-4 sm:max-w-[96%] md:max-w-[92%] md:px-5 md:py-5">
                  <div className="chat-markdown">
                    <ReactMarkdown remarkPlugins={[remarkMath]} rehypePlugins={[rehypeKatex]}>
                      {response.answer_md}
                    </ReactMarkdown>
                  </div>
                </div>
                {response.citations.length > 0 ? (
                  <div className="max-w-full rounded-3xl border border-white/10 bg-white/5 p-4 sm:max-w-[96%] md:max-w-[92%]">
                    <p className="text-xs uppercase tracking-[0.24em] text-brand">引用来源</p>
                    <div className="mt-3 flex flex-wrap gap-2">
                      {response.citations.map((citation, index) => (
                        <span
                          key={`${turn.id}-${citation.chunk_id}-${index}`}
                          className="rounded-full border border-white/10 px-3 py-2 text-xs text-mist"
                        >
                          {citation.section_title} · p.{citation.page_num}
                        </span>
                      ))}
                    </div>
                  </div>
                ) : null}
                {response.suggested_followups.length > 0 ? (
                  <div className="max-w-full rounded-3xl border border-white/10 bg-white/5 p-4 sm:max-w-[96%] md:max-w-[92%]">
                    <p className="text-xs uppercase tracking-[0.24em] text-brand">猜你想问</p>
                    <div className="mt-3 flex flex-wrap gap-2">
                      {response.suggested_followups.map((item) => (
                        <button
                          key={`${turn.id}-${item}`}
                          type="button"
                          onClick={() => setDraftQuestion(paperId, item)}
                          className="rounded-full border border-white/10 px-3 py-2 text-xs text-mist"
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
          </div>
        ) : (
          <div className="flex h-full items-center justify-center">
            <div className="max-w-xl text-center">
              <p className="text-sm text-mist">开始提问。</p>
            </div>
          </div>
        )}
      </div>

      <div className="shrink-0 border-t border-white/10 bg-ink/70 px-4 py-4 backdrop-blur-xl md:px-6">
        <div className="rounded-[24px] border border-white/10 bg-black/20 p-3 md:rounded-[28px]">
          <textarea
            value={chatState.draftQuestion}
            onChange={(event) => setDraftQuestion(paperId, event.target.value)}
            className="h-24 max-h-40 w-full resize-y bg-transparent p-2 text-sm text-white outline-none md:h-28"
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
                  );
                  appendChatTurn(paperId, {
                    id: `${result.message_id}-${Date.now()}`,
                    question: chatState.draftQuestion,
                    response: result,
                  });
                })
              }
              className="w-full rounded-full bg-brand px-5 py-3 text-sm font-medium text-black sm:w-auto"
            >
              {isPending ? "思考中..." : "发送"}
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}
