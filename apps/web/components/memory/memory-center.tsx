"use client";

import { useState } from "react";

import { EntityMemoryPanel } from "@/components/memory/entity-memory-panel";
import { PaperEntityMemoryPanel } from "@/components/memory/paper-entity-memory-panel";
import { SessionMemoryPanel } from "@/components/memory/session-memory-panel";
import { SessionSummaryPanel } from "@/components/memory/session-summary-panel";
import type {
  PaperCard,
  PaperEntityMemoryCard,
  SessionMemoryView,
  SessionSummaryView,
  UserEntityMemory,
} from "@/types";

type MemoryCenterProps = {
  instantMemoryItems: SessionMemoryView[];
  summaryItems: SessionSummaryView[];
  userMemory: UserEntityMemory;
  papers: PaperCard[];
  paperMemoryItems: PaperEntityMemoryCard[];
};

type MemorySectionId = "instant" | "summary" | "entity" | "paper";

const sections: Array<{ id: MemorySectionId; label: string; description: string }> = [
  { id: "instant", label: "瞬时记忆", description: "最近窗口内的原始对话上下文" },
  { id: "summary", label: "短时记忆", description: "窗口外历史的会话压缩摘要" },
  { id: "entity", label: "实体记忆", description: "用户级共享背景与理解状态" },
  { id: "paper", label: "论文记忆", description: "每篇论文的结构化记忆卡片" },
];

export function MemoryCenter({
  instantMemoryItems,
  summaryItems,
  userMemory,
  papers,
  paperMemoryItems,
}: MemoryCenterProps) {
  const [activeSection, setActiveSection] = useState<MemorySectionId>("instant");

  return (
    <div className="space-y-4">
      <section className="glass-panel bg-hero-grid p-8 shadow-glow">
        <p className="text-xs uppercase tracking-[0.3em] text-brand">Memory Center</p>
        <h2 className="mt-3 text-4xl font-semibold text-slate-900">记忆中心</h2>
        <p className="mt-4 max-w-3xl text-sm leading-7 text-slate-700">
          把瞬时记忆、短时记忆、实体记忆和论文记忆统一放在一个入口里，按层查看当前系统里不同类型的记忆状态。
        </p>
      </section>

      <section className="glass-panel p-4">
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          {sections.map((section) => {
            const selected = section.id === activeSection;
            return (
              <button
                key={section.id}
                type="button"
                onClick={() => setActiveSection(section.id)}
                className={`rounded-[1.5rem] border px-4 py-4 text-left transition ${
                  selected ? "border-brand/50 bg-brand/15" : "border-black/10 bg-white/60"
                }`}
              >
                <p className="text-xs uppercase tracking-[0.24em] text-slate-600">{section.label}</p>
                <p className="mt-2 text-sm leading-6 text-slate-800">{section.description}</p>
              </button>
            );
          })}
        </div>
      </section>

      {activeSection === "instant" ? <SessionMemoryPanel initialItems={instantMemoryItems} /> : null}
      {activeSection === "summary" ? <SessionSummaryPanel initialItems={summaryItems} /> : null}
      {activeSection === "entity" ? (
        <EntityMemoryPanel initialMemory={userMemory} initialPapers={papers} />
      ) : null}
      {activeSection === "paper" ? <PaperEntityMemoryPanel initialItems={paperMemoryItems} /> : null}
    </div>
  );
}
