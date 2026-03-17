import type {
  ChatConversation,
  ChatHistoryMessage,
  ChatModelOption,
  ChatResponse,
  LongTermMemoryListResponse,
  MemoryWriteInspectResponse,
  MemoryItem,
  MemoryItemListResponse,
  MemoryOverview,
  Overview,
  PaperCard,
  PaperEntityMemoryCard,
  PaperEntityMemoryListResponse,
  ReadingMemory,
  SessionMemoryListResponse,
  SessionMemoryView,
  SessionSummaryListResponse,
  SessionSummaryView,
  UserEntityMemory,
} from "@/types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error(`Request failed: ${path}`);
  }
  return response.json() as Promise<T>;
}

export async function fetchPapers() {
  return getJson<PaperCard[]>("/papers");
}

export async function updatePaperMetadata(
  paperId: string,
  payload: { category?: string | null; tags?: string[] },
) {
  const response = await fetch(`${API_BASE_URL}/papers/${paperId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error("Update paper failed");
  }
  return response.json() as Promise<PaperCard>;
}

export async function deletePaper(paperId: string) {
  const response = await fetch(`${API_BASE_URL}/papers/${paperId}`, {
    method: "DELETE",
  });
  if (!response.ok) {
    throw new Error("Delete paper failed");
  }
}

export async function fetchOverview(paperId: string) {
  return getJson<Overview>(`/papers/${paperId}/overview`);
}

export async function fetchPaperStructure(paperId: string) {
  return getJson(`/papers/${paperId}/structure`);
}

export async function fetchMemoryOverview() {
  return getJson<MemoryOverview>("/memory/overview");
}

export async function fetchLongTermMemories() {
  return getJson<LongTermMemoryListResponse>("/memory/long-term");
}

export async function inspectMemoryWritePolicy(payload: {
  source_type: string;
  session_id?: string | null;
  paper_id?: string | null;
  user_id?: string;
  question: string;
  answer?: string | null;
}) {
  const response = await fetch(`${API_BASE_URL}/memory/write-policy/inspect`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error("Inspect memory write policy failed");
  }
  return response.json() as Promise<MemoryWriteInspectResponse>;
}

export async function fetchPaperMemory(paperId: string) {
  return getJson<ReadingMemory>(`/memory/papers/${paperId}`);
}

export async function fetchUserEntityMemory() {
  return getJson<UserEntityMemory>("/memory/user");
}

export async function fetchPaperEntityMemories() {
  return getJson<PaperEntityMemoryListResponse>("/memory/paper-entities");
}

export async function fetchPaperEntityMemory(paperId: string) {
  return getJson<PaperEntityMemoryCard>(`/memory/paper-entities/${paperId}`);
}

export async function fetchMemoryItems(params?: {
  scope?: string;
  paper_id?: string;
  memory_type?: string;
  enabled?: string;
}) {
  const query = new URLSearchParams();
  if (params?.scope) query.set("scope", params.scope);
  if (params?.paper_id) query.set("paper_id", params.paper_id);
  if (params?.memory_type) query.set("memory_type", params.memory_type);
  if (params?.enabled) query.set("enabled", params.enabled);
  const suffix = query.toString() ? `?${query.toString()}` : "";
  return getJson<MemoryItemListResponse>(`/memory/items${suffix}`);
}

export async function fetchMemoryItem(memoryId: string) {
  return getJson<MemoryItem>(`/memory/items/${memoryId}`);
}

export async function setMemoryItemEnabled(memoryId: string, enabled: boolean) {
  const response = await fetch(
    `${API_BASE_URL}/memory/items/${memoryId}/${enabled ? "enable" : "disable"}`,
    { method: "POST" },
  );
  if (!response.ok) {
    throw new Error("Memory toggle failed");
  }
  return response.json() as Promise<MemoryItem>;
}

export async function deleteMemoryItem(memoryId: string) {
  const response = await fetch(`${API_BASE_URL}/memory/items/${memoryId}`, {
    method: "DELETE",
  });
  if (!response.ok) {
    throw new Error("Delete memory failed");
  }
}

export async function resetMemory(payload: {
  scope?: string | null;
  paper_id?: string | null;
  memory_type?: string | null;
}) {
  const response = await fetch(`${API_BASE_URL}/memory/reset`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error("Reset memory failed");
  }
  return response.json() as Promise<{ deleted: number }>;
}

export async function fetchSessionMemories() {
  return getJson<SessionMemoryListResponse>("/memory/session-memories");
}

export async function fetchSessionMemory(conversationId: string) {
  return getJson<SessionMemoryView>(`/memory/session-memories/${conversationId}`);
}

export async function clearSessionMemory(conversationId: string) {
  const response = await fetch(`${API_BASE_URL}/memory/session-memories/${conversationId}/clear`, {
    method: "POST",
  });
  if (!response.ok) {
    throw new Error("Clear session memory failed");
  }
  return response.json() as Promise<SessionMemoryView>;
}

export async function fetchSessionSummaries() {
  return getJson<SessionSummaryListResponse>("/memory/session-summaries");
}

export async function fetchSessionSummary(conversationId: string) {
  return getJson<SessionSummaryView>(`/memory/session-summaries/${conversationId}`);
}

export async function fetchChatModels() {
  return getJson<ChatModelOption[]>("/chat/models");
}

export async function getOrCreatePaperConversation(paperId: string) {
  return getJson<ChatConversation>(
    `/chat/sessions/by-paper/${paperId}`,
  );
}

export async function fetchGlobalConversations() {
  return getJson<{ conversations: ChatConversation[] }>("/chat/conversations/global");
}

export async function createGlobalConversation(title?: string) {
  const response = await fetch(`${API_BASE_URL}/chat/conversations/global`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title }),
  });
  if (!response.ok) {
    throw new Error("Create global conversation failed");
  }
  return response.json() as Promise<ChatConversation>;
}

export async function deleteGlobalConversation(conversationId: string) {
  const response = await fetch(`${API_BASE_URL}/chat/conversations/global/${conversationId}`, {
    method: "DELETE",
  });
  if (!response.ok) {
    throw new Error("Delete global conversation failed");
  }
}

export async function fetchChatMessages(conversationId: string) {
  return getJson<ChatHistoryMessage[]>(`/chat/sessions/${conversationId}/messages`);
}

export async function fetchIngestionJob(jobId: string) {
  return getJson<{
    job_id: string;
    paper_id: string;
    status: string;
    stage: string;
    progress: number;
  }>(`/ingestion/jobs/${jobId}`);
}

export async function askQuestion(
  paperId: string | null | undefined,
  question: string,
  selectedModel?: string,
  enableThinking?: boolean,
  conversationId?: string,
) {
  const resolvedConversationId =
    conversationId ?? (paperId ? await getOrCreatePaperConversation(paperId) : await createGlobalConversation()).conversation_id;

  const response = await fetch(
    `${API_BASE_URL}/chat/sessions/${resolvedConversationId}/messages`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        paper_id: paperId,
        question,
        selected_model: selectedModel,
        enable_thinking: enableThinking,
      }),
    },
  );
  if (!response.ok) {
    throw new Error("Chat request failed");
  }
  return response.json() as Promise<ChatResponse>;
}
