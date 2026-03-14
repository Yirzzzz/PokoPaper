"use client";

import { create } from "zustand";

import type { ChatConversation, ChatHistoryMessage, ChatResponse } from "@/types";

type ChatTurn = {
  id: string;
  question: string;
  response: ChatResponse;
};

type ChatState = {
  conversationId: string | null;
  draftQuestion: string;
  selectedModel: string;
  enableThinking: boolean;
  turns: ChatTurn[];
  historyLoaded: boolean;
  historyMessages: ChatHistoryMessage[];
};

type AppState = {
  activePaperId: string;
  activeGlobalConversationId: string | null;
  globalConversations: ChatConversation[];
  chatStates: Record<string, ChatState>;
  setActivePaperId: (paperId: string) => void;
  setActiveGlobalConversationId: (conversationId: string | null) => void;
  setGlobalConversations: (conversations: ChatConversation[]) => void;
  upsertGlobalConversation: (conversation: ChatConversation) => void;
  removeGlobalConversation: (conversationId: string) => void;
  initializeChatState: (chatKey: string, initialQuestion: string) => void;
  setConversationId: (chatKey: string, conversationId: string) => void;
  hydrateChatHistory: (chatKey: string, messages: ChatHistoryMessage[]) => void;
  setDraftQuestion: (chatKey: string, question: string) => void;
  setSelectedModel: (chatKey: string, modelId: string) => void;
  setEnableThinking: (chatKey: string, enabled: boolean) => void;
  appendChatTurn: (chatKey: string, turn: ChatTurn) => void;
};

function createDefaultChatState(initialQuestion: string): ChatState {
  return {
    conversationId: null,
    draftQuestion: initialQuestion,
    selectedModel: "",
    enableThinking: false,
    turns: [],
    historyLoaded: false,
    historyMessages: [],
  };
}

function getStoredValue(key: string, fallback: string | null): string | null {
  if (typeof window === "undefined") {
    return fallback;
  }
  return window.localStorage.getItem(key) ?? fallback;
}

export const useAppStore = create<AppState>((set) => ({
  activePaperId: getStoredValue("pokomon-active-paper-id", "paper-demo-001") ?? "paper-demo-001",
  activeGlobalConversationId: getStoredValue("pokomon-active-global-conversation-id", null),
  globalConversations: [],
  chatStates: {},
  setActivePaperId: (activePaperId) => {
    if (typeof window !== "undefined") {
      window.localStorage.setItem("pokomon-active-paper-id", activePaperId);
    }
    set({ activePaperId });
  },
  setActiveGlobalConversationId: (activeGlobalConversationId) => {
    if (typeof window !== "undefined") {
      if (activeGlobalConversationId) {
        window.localStorage.setItem("pokomon-active-global-conversation-id", activeGlobalConversationId);
      } else {
        window.localStorage.removeItem("pokomon-active-global-conversation-id");
      }
    }
    set({ activeGlobalConversationId });
  },
  setGlobalConversations: (globalConversations) => set({ globalConversations }),
  upsertGlobalConversation: (conversation) =>
    set((state) => {
      const remaining = state.globalConversations.filter(
        (item) => item.conversation_id !== conversation.conversation_id,
      );
      return {
        globalConversations: [conversation, ...remaining].sort(
          (left, right) => right.updated_at.localeCompare(left.updated_at),
        ),
      };
    }),
  removeGlobalConversation: (conversationId) =>
    set((state) => {
      const globalConversations = state.globalConversations.filter(
        (item) => item.conversation_id !== conversationId,
      );
      const nextActive =
        state.activeGlobalConversationId === conversationId
          ? globalConversations[0]?.conversation_id ?? null
          : state.activeGlobalConversationId;
      const { [conversationId]: _removed, ...remainingChatStates } = state.chatStates;
      if (typeof window !== "undefined") {
        if (nextActive) {
          window.localStorage.setItem("pokomon-active-global-conversation-id", nextActive);
        } else {
          window.localStorage.removeItem("pokomon-active-global-conversation-id");
        }
      }
      return {
        globalConversations,
        activeGlobalConversationId: nextActive,
        chatStates: remainingChatStates,
      };
    }),
  initializeChatState: (chatKey, initialQuestion) =>
    set((state) => ({
      chatStates: state.chatStates[chatKey]
        ? state.chatStates
        : {
            ...state.chatStates,
            [chatKey]: createDefaultChatState(initialQuestion),
          },
    })),
  setConversationId: (chatKey, conversationId) =>
    set((state) => ({
      chatStates: {
        ...state.chatStates,
        [chatKey]: {
          ...(state.chatStates[chatKey] ?? createDefaultChatState("")),
          conversationId,
        },
      },
    })),
  hydrateChatHistory: (chatKey, messages) =>
    set((state) => ({
      chatStates: {
        ...state.chatStates,
        [chatKey]: {
          ...(state.chatStates[chatKey] ?? createDefaultChatState("")),
          historyLoaded: true,
          historyMessages: messages,
          turns: [],
        },
      },
    })),
  setDraftQuestion: (chatKey, question) =>
    set((state) => ({
      chatStates: {
        ...state.chatStates,
        [chatKey]: {
          ...(state.chatStates[chatKey] ?? createDefaultChatState("")),
          draftQuestion: question,
        },
      },
    })),
  setSelectedModel: (chatKey, modelId) =>
    set((state) => ({
      chatStates: {
        ...state.chatStates,
        [chatKey]: {
          ...(state.chatStates[chatKey] ?? createDefaultChatState("")),
          selectedModel: modelId,
        },
      },
    })),
  setEnableThinking: (chatKey, enabled) =>
    set((state) => ({
      chatStates: {
        ...state.chatStates,
        [chatKey]: {
          ...(state.chatStates[chatKey] ?? createDefaultChatState("")),
          enableThinking: enabled,
        },
      },
    })),
  appendChatTurn: (chatKey, turn) =>
    set((state) => ({
      chatStates: {
        ...state.chatStates,
        [chatKey]: {
          ...(state.chatStates[chatKey] ?? createDefaultChatState("")),
          turns: [...(state.chatStates[chatKey]?.turns ?? []), turn],
        },
      },
    })),
}));
