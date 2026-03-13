import type {
  ChatHistoryMessage,
  ChatModelOption,
  ChatResponse,
  MemoryOverview,
  Overview,
  PaperCard,
  ReadingMemory,
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

export async function fetchPaperMemory(paperId: string) {
  return getJson<ReadingMemory>(`/memory/papers/${paperId}`);
}

export async function fetchChatModels() {
  return getJson<ChatModelOption[]>("/chat/models");
}

export async function getOrCreateChatSession(paperId: string) {
  return getJson<{ session_id: string; paper_id: string; title: string }>(
    `/chat/sessions/by-paper/${paperId}`,
  );
}

export async function fetchChatMessages(sessionId: string) {
  return getJson<ChatHistoryMessage[]>(`/chat/sessions/${sessionId}/messages`);
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
  paperId: string,
  question: string,
  selectedModel?: string,
  enableThinking?: boolean,
) {
  const session = await getOrCreateChatSession(paperId);

  const response = await fetch(
    `${API_BASE_URL}/chat/sessions/${session.session_id}/messages`,
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
