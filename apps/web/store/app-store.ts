"use client";

import { create } from "zustand";

import type { ChatHistoryMessage, ChatResponse } from "@/types";

type ChatTurn = {
  id: string;
  question: string;
  response: ChatResponse;
};

type PaperChatState = {
  sessionId: string | null;
  draftQuestion: string;
  selectedModel: string;
  enableThinking: boolean;
  turns: ChatTurn[];
  historyLoaded: boolean;
  historyMessages: ChatHistoryMessage[];
};

type AppState = {
  activePaperId: string;
  paperChats: Record<string, PaperChatState>;
  setActivePaperId: (paperId: string) => void;
  initializePaperChat: (paperId: string, initialQuestion: string) => void;
  setSessionId: (paperId: string, sessionId: string) => void;
  hydrateChatHistory: (paperId: string, messages: ChatHistoryMessage[]) => void;
  setDraftQuestion: (paperId: string, question: string) => void;
  setSelectedModel: (paperId: string, modelId: string) => void;
  setEnableThinking: (paperId: string, enabled: boolean) => void;
  appendChatTurn: (paperId: string, turn: ChatTurn) => void;
};

export const useAppStore = create<AppState>((set) => ({
  activePaperId: "paper-demo-001",
  paperChats: {},
  setActivePaperId: (activePaperId) => set({ activePaperId }),
  initializePaperChat: (paperId, initialQuestion) =>
    set((state) => ({
      paperChats: state.paperChats[paperId]
        ? state.paperChats
        : {
            ...state.paperChats,
            [paperId]: {
              sessionId: null,
              draftQuestion: initialQuestion,
              selectedModel: "",
              enableThinking: false,
              turns: [],
              historyLoaded: false,
              historyMessages: [],
            },
          },
    })),
  setSessionId: (paperId, sessionId) =>
    set((state) => ({
      paperChats: {
        ...state.paperChats,
        [paperId]: {
          ...(state.paperChats[paperId] ?? {
            sessionId: null,
            draftQuestion: "",
            selectedModel: "",
            enableThinking: false,
            turns: [],
            historyLoaded: false,
            historyMessages: [],
          }),
          sessionId,
        },
      },
    })),
  hydrateChatHistory: (paperId, messages) =>
    set((state) => ({
      paperChats: {
        ...state.paperChats,
        [paperId]: {
          ...(state.paperChats[paperId] ?? {
            sessionId: null,
            draftQuestion: "",
            selectedModel: "",
            enableThinking: false,
            turns: [],
            historyLoaded: false,
            historyMessages: [],
          }),
          historyLoaded: true,
          historyMessages: messages,
        },
      },
    })),
  setDraftQuestion: (paperId, question) =>
    set((state) => ({
      paperChats: {
        ...state.paperChats,
        [paperId]: {
          ...(state.paperChats[paperId] ?? {
            sessionId: null,
            draftQuestion: "",
            selectedModel: "",
            enableThinking: false,
            turns: [],
            historyLoaded: false,
            historyMessages: [],
          }),
          draftQuestion: question,
        },
      },
    })),
  setSelectedModel: (paperId, modelId) =>
    set((state) => ({
      paperChats: {
        ...state.paperChats,
        [paperId]: {
          ...(state.paperChats[paperId] ?? {
            sessionId: null,
            draftQuestion: "",
            selectedModel: "",
            enableThinking: false,
            turns: [],
            historyLoaded: false,
            historyMessages: [],
          }),
          selectedModel: modelId,
        },
      },
    })),
  setEnableThinking: (paperId, enabled) =>
    set((state) => ({
      paperChats: {
        ...state.paperChats,
        [paperId]: {
          ...(state.paperChats[paperId] ?? {
            sessionId: null,
            draftQuestion: "",
            selectedModel: "",
            enableThinking: false,
            turns: [],
            historyLoaded: false,
            historyMessages: [],
          }),
          enableThinking: enabled,
        },
      },
    })),
  appendChatTurn: (paperId, turn) =>
    set((state) => ({
      paperChats: {
        ...state.paperChats,
        [paperId]: {
          ...(state.paperChats[paperId] ?? {
            sessionId: null,
            draftQuestion: "",
            selectedModel: "",
            enableThinking: false,
            turns: [],
            historyLoaded: false,
            historyMessages: [],
          }),
          turns: [...(state.paperChats[paperId]?.turns ?? []), turn],
        },
      },
    })),
}));
