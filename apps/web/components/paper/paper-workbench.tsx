"use client";

import { useMemo, useState } from "react";

import { ChatPanel } from "@/components/chat/chat-panel";
import { FormulaBlock } from "@/components/paper/formula-block";
import { OverviewCard } from "@/components/paper/overview-card";
import { MemoryPanel } from "@/components/memory/memory-panel";
import type { Overview, ReadingMemory, MemoryOverview } from "@/types";

type TabId =
  | "overview"
  | "motivation"
  | "method"
  | "experiments"
  | "chat"
  | "reading"
  | "memory";

type PaperWorkbenchProps = {
  paperId: string;
  overview: Overview;
  paperMemory: ReadingMemory;
  memoryOverview: MemoryOverview;
};

const tabs: Array<{ id: TabId; label: string }> = [
  { id: "overview", label: "概览" },
  { id: "motivation", label: "特性" },
  { id: "method", label: "技能" },
  { id: "experiments", label: "对战" },
  { id: "chat", label: "追问" },
  { id: "reading", label: "进化路线" },
  { id: "memory", label: "档案" },
];

export function PaperWorkbench({
  paperId,
  overview,
  paperMemory,
  memoryOverview,
}: PaperWorkbenchProps) {
  const [activeTab, setActiveTab] = useState<TabId>("overview");

  const content = useMemo(() => {
    if (activeTab === "overview") {
      return (
        <div className="grid gap-4">
          <OverviewCard eyebrow="TL;DR" title="一眼看懂这篇论文">
            {overview.tldr}
          </OverviewCard>
          <OverviewCard eyebrow="问题定义" title="这篇论文在解决什么">
            {overview.problem_definition}
          </OverviewCard>
          <OverviewCard eyebrow="结论" title="论文最终结论">
            {overview.conclusion}
          </OverviewCard>
        </div>
      );
    }

    if (activeTab === "motivation") {
      return (
        <div className="grid gap-4">
          <OverviewCard eyebrow="动机" title="研究动机">
            {overview.research_motivation}
          </OverviewCard>
          <OverviewCard eyebrow="贡献" title="主要贡献">
            <ul className="space-y-2">
              {overview.main_contributions.map((item, index) => (
                <li key={`${item}-${index}`}>{item}</li>
              ))}
            </ul>
          </OverviewCard>
          <OverviewCard eyebrow="迁移启发" title="可迁移点">
            <div className="space-y-4">
              {overview.transferable_insights.map((item, index) => (
                <div key={`${item.idea}-${index}`} className="rounded-3xl border border-black/10 bg-white/55 p-4">
                  <p className="text-slate-900">{item.idea}</p>
                  <p className="mt-2 text-sm leading-7 text-slate-700">{item.how_to_apply}</p>
                </div>
              ))}
            </div>
          </OverviewCard>
        </div>
      );
    }

    if (activeTab === "method") {
      return (
        <div className="grid gap-4">
          <OverviewCard eyebrow="方法主线" title="主线">
            {overview.method_summary}
          </OverviewCard>
          <OverviewCard eyebrow="关键模块" title="哪个模块起作用">
            <div className="space-y-4">
              {overview.key_modules.map((module, index) => (
                <div key={`${module.name}-${index}`} className="rounded-3xl border border-black/10 bg-white/55 p-4">
                  <p className="text-base font-medium text-slate-900">{module.name}</p>
                  <p className="mt-2 text-sm leading-7 text-slate-700">{module.purpose}</p>
                  <p className="mt-2 text-sm leading-7 text-emerald-800">{module.why_it_matters}</p>
                </div>
              ))}
            </div>
          </OverviewCard>
          <OverviewCard eyebrow="关键公式" title="公式与变量解释">
            <div className="space-y-4">
              {overview.key_formulas.map((formula, index) => (
                <FormulaBlock
                  key={`${formula.formula_id}-${index}`}
                  latex={formula.latex}
                  explanation={formula.explanation}
                  variables={formula.variables}
                />
              ))}
            </div>
          </OverviewCard>
        </div>
      );
    }

    if (activeTab === "experiments") {
      return (
        <div className="grid gap-4">
          <OverviewCard eyebrow="实验结论" title="实验证明了什么">
            <div className="space-y-4">
              {overview.main_experiments.map((item, index) => (
                <div key={`${item.claim}-${index}`} className="rounded-3xl border border-black/10 bg-white/55 p-4">
                  <p className="text-slate-900">{item.claim}</p>
                  <p className="mt-2 text-sm leading-7 text-slate-700">{item.evidence}</p>
                  {item.what_it_proves ? (
                    <p className="mt-2 text-sm leading-7 text-emerald-800">它证明了：{item.what_it_proves}</p>
                  ) : null}
                </div>
              ))}
            </div>
          </OverviewCard>
          <OverviewCard eyebrow="局限性" title="这篇论文的边界">
            <ul className="space-y-2">
              {overview.limitations.map((item, index) => (
                <li key={`${item}-${index}`}>{item}</li>
              ))}
            </ul>
          </OverviewCard>
        </div>
      );
    }

    if (activeTab === "reading") {
      return (
        <div className="grid gap-4">
          <OverviewCard eyebrow="推荐阅读" title="下一步">
            <div className="space-y-4">
              {overview.recommended_readings.map((item, index) => (
                <div key={`${item.title}-${index}`} className="rounded-3xl border border-black/10 bg-white/55 p-4">
                  <p className="text-slate-900">{item.title}</p>
                  <p className="mt-2 text-sm leading-7 text-slate-700">{item.reason}</p>
                  <p className="mt-2 text-xs text-emerald-800">
                    {item.difficulty_level} · {item.suggested_section}
                  </p>
                </div>
              ))}
            </div>
          </OverviewCard>
          <OverviewCard eyebrow="前置知识" title="先补这些">
            <div className="space-y-4">
              {overview.prerequisite_knowledge.map((item, index) => (
                <div key={`${item.topic}-${index}`} className="rounded-3xl border border-black/10 bg-white/55 p-4">
                  <p className="text-slate-900">{item.topic}</p>
                  <p className="mt-2 text-sm leading-7 text-slate-700">{item.reason}</p>
                </div>
              ))}
            </div>
          </OverviewCard>
        </div>
      );
    }

    if (activeTab === "memory") {
      return <MemoryPanel overview={memoryOverview} paperMemory={paperMemory} />;
    }

    return <ChatPanel paperId={paperId} />;
  }, [activeTab, memoryOverview, overview, paperId, paperMemory]);

  return (
    <div className="grid gap-4 xl:grid-cols-[220px_minmax(0,1fr)]">
      <nav className="glass-panel p-5">
        <ul className="space-y-2 text-sm text-slate-700">
          {tabs.map((tab) => (
            <li key={tab.id}>
              <button
                type="button"
                onClick={() => setActiveTab(tab.id)}
                className={`w-full rounded-2xl px-4 py-3 text-left transition ${
                  activeTab === tab.id
                    ? "bg-brand/10 text-slate-900"
                    : "text-slate-700 hover:bg-white/55 hover:text-slate-900"
                }`}
              >
                {tab.label}
              </button>
            </li>
          ))}
        </ul>
      </nav>
      <div className="grid gap-4">{content}</div>
    </div>
  );
}
