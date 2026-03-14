"use client";

import { useEffect, useMemo, useState } from "react";
import { Loader2, RotateCcw, ToggleLeft, ToggleRight, Trash2 } from "lucide-react";

import {
  deleteMemoryItem,
  fetchMemoryItems,
  fetchPapers,
  resetMemory,
  setMemoryItemEnabled,
} from "@/lib/api/client";
import type { MemoryItem, PaperCard } from "@/types";

type Filters = {
  scope: string;
  memoryType: string;
  paperId: string;
  enabled: string;
};

const defaultFilters: Filters = {
  scope: "all",
  memoryType: "all",
  paperId: "all",
  enabled: "all",
};

function formatDate(value?: string | null) {
  if (!value) return "—";
  return new Date(value).toLocaleString("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function MemoryLab() {
  const [items, setItems] = useState<MemoryItem[]>([]);
  const [papers, setPapers] = useState<PaperCard[]>([]);
  const [filters, setFilters] = useState<Filters>(defaultFilters);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [busyAction, setBusyAction] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    try {
      const [itemResponse, paperResponse] = await Promise.all([
        fetchMemoryItems(),
        fetchPapers(),
      ]);
      setItems(itemResponse.items);
      setPapers(paperResponse);
      setSelectedId((current) => current && itemResponse.items.some((item) => item.memory_id === current) ? current : itemResponse.items[0]?.memory_id ?? null);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  const filteredItems = useMemo(() => {
    return items.filter((item) => {
      if (filters.scope !== "all" && item.scope_type !== filters.scope) return false;
      if (filters.memoryType !== "all" && item.memory_type !== filters.memoryType) return false;
      if (filters.paperId !== "all" && item.paper_id !== filters.paperId) return false;
      if (filters.enabled === "enabled" && !item.is_enabled) return false;
      if (filters.enabled === "disabled" && item.is_enabled) return false;
      return true;
    });
  }, [filters, items]);

  const selectedItem = filteredItems.find((item) => item.memory_id === selectedId) ?? filteredItems[0] ?? null;

  const stats = useMemo(
    () => ({
      total: items.length,
      session: items.filter((item) => item.scope_type === "session").length,
      paper: items.filter((item) => item.scope_type === "paper").length,
      user: items.filter((item) => item.scope_type === "user").length,
      disabled: items.filter((item) => !item.is_enabled).length,
    }),
    [items],
  );

  const memoryTypes = useMemo(
    () => Array.from(new Set(items.map((item) => item.memory_type))).sort(),
    [items],
  );

  async function handleToggle(item: MemoryItem, enabled: boolean) {
    setBusyAction(item.memory_id);
    try {
      await setMemoryItemEnabled(item.memory_id, enabled);
      await load();
      setSelectedId(item.memory_id);
    } finally {
      setBusyAction(null);
    }
  }

  async function handleDelete(item: MemoryItem) {
    setBusyAction(item.memory_id);
    try {
      await deleteMemoryItem(item.memory_id);
      await load();
    } finally {
      setBusyAction(null);
    }
  }

  async function handleReset() {
    setBusyAction("reset");
    try {
      await resetMemory({
        scope: filters.scope === "all" ? null : filters.scope,
        paper_id: filters.paperId === "all" ? null : filters.paperId,
        memory_type: filters.memoryType === "all" ? null : filters.memoryType,
      });
      await load();
    } finally {
      setBusyAction(null);
    }
  }

  return (
    <section className="flex min-h-[calc(100vh-3rem)] flex-col gap-4">
      <div className="glass-panel flex flex-col gap-4 p-6">
        <div className="flex flex-col gap-1">
          <p className="text-xs uppercase tracking-[0.28em] text-brand">Memory Lab</p>
          <h1 className="text-3xl font-semibold text-slate-900">Memory Lab</h1>
        </div>
        <div className="grid gap-3 md:grid-cols-5">
          {[
            { label: "total memories", value: stats.total },
            { label: "session memories", value: stats.session },
            { label: "paper memories", value: stats.paper },
            { label: "user memories", value: stats.user },
            { label: "disabled memories", value: stats.disabled },
          ].map((stat) => (
            <div key={stat.label} className="rounded-3xl border border-black/10 bg-white/70 px-4 py-4">
              <p className="text-xs uppercase tracking-[0.22em] text-slate-500">{stat.label}</p>
              <p className="mt-2 text-2xl font-semibold text-slate-900">{stat.value}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="grid flex-1 gap-4 xl:grid-cols-[280px_minmax(0,1fr)_360px]">
        <aside className="glass-panel flex flex-col gap-4 p-5">
          <div>
            <p className="text-xs uppercase tracking-[0.24em] text-slate-500">filters</p>
            <h2 className="mt-2 text-lg font-semibold text-slate-900">Memory Filter</h2>
          </div>
          <label className="flex flex-col gap-2 text-sm text-slate-700">
            Scope
            <select
              value={filters.scope}
              onChange={(event) => setFilters((current) => ({ ...current, scope: event.target.value }))}
              className="rounded-2xl border border-black/10 bg-white/80 px-3 py-2 text-slate-900"
            >
              <option value="all">all</option>
              <option value="session">session</option>
              <option value="paper">paper</option>
              <option value="user">user</option>
            </select>
          </label>
          <label className="flex flex-col gap-2 text-sm text-slate-700">
            Memory Type
            <select
              value={filters.memoryType}
              onChange={(event) => setFilters((current) => ({ ...current, memoryType: event.target.value }))}
              className="rounded-2xl border border-black/10 bg-white/80 px-3 py-2 text-slate-900"
            >
              <option value="all">all</option>
              {memoryTypes.map((type) => (
                <option key={type} value={type}>
                  {type}
                </option>
              ))}
            </select>
          </label>
          <label className="flex flex-col gap-2 text-sm text-slate-700">
            Paper
            <select
              value={filters.paperId}
              onChange={(event) => setFilters((current) => ({ ...current, paperId: event.target.value }))}
              className="rounded-2xl border border-black/10 bg-white/80 px-3 py-2 text-slate-900"
            >
              <option value="all">all</option>
              {papers.map((paper) => (
                <option key={paper.id} value={paper.id}>
                  {paper.title}
                </option>
              ))}
            </select>
          </label>
          <label className="flex flex-col gap-2 text-sm text-slate-700">
            Status
            <select
              value={filters.enabled}
              onChange={(event) => setFilters((current) => ({ ...current, enabled: event.target.value }))}
              className="rounded-2xl border border-black/10 bg-white/80 px-3 py-2 text-slate-900"
            >
              <option value="all">all</option>
              <option value="enabled">enabled</option>
              <option value="disabled">disabled</option>
            </select>
          </label>
          <button
            type="button"
            onClick={() => setFilters(defaultFilters)}
            className="rounded-2xl border border-black/10 bg-white/70 px-3 py-2 text-sm text-slate-700"
          >
            清空过滤
          </button>
          <button
            type="button"
            onClick={() => void handleReset()}
            disabled={busyAction === "reset"}
            className="flex items-center justify-center gap-2 rounded-2xl bg-brand px-3 py-2 text-sm font-medium text-white disabled:opacity-60"
          >
            {busyAction === "reset" ? <Loader2 className="h-4 w-4 animate-spin" /> : <RotateCcw className="h-4 w-4" />}
            清理当前过滤结果
          </button>
        </aside>

        <div className="glass-panel flex min-h-[720px] flex-col overflow-hidden">
          <div className="border-b border-black/10 px-5 py-4 text-sm text-slate-700">
            {loading ? "加载中…" : `共 ${filteredItems.length} 条`}
          </div>
          <div className="flex-1 overflow-y-auto p-4">
            {loading ? (
              <div className="flex h-full items-center justify-center text-sm text-slate-600">加载中…</div>
            ) : filteredItems.length === 0 ? (
              <div className="flex h-full items-center justify-center text-sm text-slate-600">没有匹配的 memory。</div>
            ) : (
              <div className="flex flex-col gap-3">
                {filteredItems.map((item) => (
                  <button
                    type="button"
                    key={item.memory_id}
                    onClick={() => setSelectedId(item.memory_id)}
                    className={`rounded-3xl border px-4 py-4 text-left transition ${
                      selectedItem?.memory_id === item.memory_id
                        ? "border-brand/40 bg-brand/10"
                        : "border-black/10 bg-white/70 hover:border-brand/25"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="text-xs uppercase tracking-[0.22em] text-slate-500">{item.memory_type}</p>
                        <p className="mt-2 line-clamp-2 text-sm font-medium text-slate-900">{item.summary}</p>
                      </div>
                      <span
                        className={`rounded-full px-2 py-1 text-[11px] font-medium ${
                          item.is_enabled ? "bg-emerald-100 text-emerald-700" : "bg-slate-200 text-slate-600"
                        }`}
                      >
                        {item.is_enabled ? "enabled" : "disabled"}
                      </span>
                    </div>
                    <div className="mt-3 flex flex-wrap gap-2 text-xs text-slate-600">
                      <span className="rounded-full bg-slate-100 px-2 py-1">{item.scope}</span>
                      {item.paper_title ? <span className="rounded-full bg-slate-100 px-2 py-1">{item.paper_title}</span> : null}
                      <span className="rounded-full bg-slate-100 px-2 py-1">{formatDate(item.updated_at || item.created_at)}</span>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        <aside className="glass-panel flex min-h-[720px] flex-col p-5">
          {selectedItem ? (
            <>
              <div className="border-b border-black/10 pb-4">
                <p className="text-xs uppercase tracking-[0.24em] text-slate-500">detail</p>
                <h2 className="mt-2 text-xl font-semibold text-slate-900">{selectedItem.memory_type}</h2>
              </div>
              <div className="mt-4 flex flex-col gap-4 overflow-y-auto text-sm text-slate-700">
                <div className="grid gap-2 rounded-3xl border border-black/10 bg-white/70 p-4">
                  <div><span className="text-slate-500">memory_id:</span> <span className="break-all text-slate-900">{selectedItem.memory_id}</span></div>
                  <div><span className="text-slate-500">scope:</span> <span className="text-slate-900">{selectedItem.scope}</span></div>
                  <div><span className="text-slate-500">paper:</span> <span className="text-slate-900">{selectedItem.paper_title ?? "—"}</span></div>
                  <div><span className="text-slate-500">created_at:</span> <span className="text-slate-900">{formatDate(selectedItem.created_at)}</span></div>
                  <div><span className="text-slate-500">updated_at:</span> <span className="text-slate-900">{formatDate(selectedItem.updated_at)}</span></div>
                  <div><span className="text-slate-500">write_reason:</span> <span className="text-slate-900">{selectedItem.write_reason ?? "—"}</span></div>
                  <div><span className="text-slate-500">write_confidence:</span> <span className="text-slate-900">{selectedItem.write_confidence ?? "—"}</span></div>
                  <div><span className="text-slate-500">status:</span> <span className="text-slate-900">{selectedItem.is_enabled ? "enabled" : "disabled"}</span></div>
                </div>
                <div className="rounded-3xl border border-black/10 bg-white/70 p-4">
                  <p className="text-xs uppercase tracking-[0.22em] text-slate-500">payload</p>
                  <pre className="mt-3 overflow-x-auto whitespace-pre-wrap text-xs text-slate-800">
                    {JSON.stringify(selectedItem.payload, null, 2)}
                  </pre>
                </div>
                <div className="rounded-3xl border border-black/10 bg-white/70 p-4">
                  <p className="text-xs uppercase tracking-[0.22em] text-slate-500">source question</p>
                  <p className="mt-3 whitespace-pre-wrap text-sm text-slate-900">{selectedItem.source_question ?? "—"}</p>
                </div>
                <div className="rounded-3xl border border-black/10 bg-white/70 p-4">
                  <p className="text-xs uppercase tracking-[0.22em] text-slate-500">source answer preview</p>
                  <p className="mt-3 whitespace-pre-wrap text-sm text-slate-900">{selectedItem.source_answer_preview ?? "—"}</p>
                </div>
              </div>
              <div className="mt-4 flex gap-2 border-t border-black/10 pt-4">
                <button
                  type="button"
                  onClick={() => void handleToggle(selectedItem, !selectedItem.is_enabled)}
                  disabled={busyAction === selectedItem.memory_id}
                  className="flex flex-1 items-center justify-center gap-2 rounded-2xl border border-black/10 bg-white/80 px-3 py-2 text-sm text-slate-800 disabled:opacity-60"
                >
                  {selectedItem.is_enabled ? <ToggleLeft className="h-4 w-4" /> : <ToggleRight className="h-4 w-4" />}
                  {selectedItem.is_enabled ? "disable" : "enable"}
                </button>
                <button
                  type="button"
                  onClick={() => void handleDelete(selectedItem)}
                  disabled={busyAction === selectedItem.memory_id}
                  className="flex flex-1 items-center justify-center gap-2 rounded-2xl bg-red-500 px-3 py-2 text-sm font-medium text-white disabled:opacity-60"
                >
                  {busyAction === selectedItem.memory_id ? <Loader2 className="h-4 w-4 animate-spin" /> : <Trash2 className="h-4 w-4" />}
                  delete
                </button>
              </div>
            </>
          ) : (
            <div className="flex h-full items-center justify-center text-sm text-slate-600">选择一条 memory 查看详情。</div>
          )}
        </aside>
      </div>
    </section>
  );
}
