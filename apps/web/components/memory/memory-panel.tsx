import type { MemoryOverview, ReadingMemory } from "@/types";

type MemoryPanelProps = {
  overview: MemoryOverview;
  paperMemory: ReadingMemory;
};

export function MemoryPanel({ overview, paperMemory }: MemoryPanelProps) {
  return (
    <div className="grid gap-4">
      <section className="glass-panel p-6">
        <p className="text-xs uppercase tracking-[0.24em] text-brand">档案</p>
        <div className="mt-4 grid gap-4 md:grid-cols-2">
          <div>
            <p className="text-sm text-slate-700">已读论文</p>
            <p className="mt-2 text-3xl font-semibold text-slate-900">{overview.read_papers}</p>
          </div>
          <div>
            <p className="text-sm text-slate-700">讲解方式</p>
            <p className="mt-2 text-lg text-slate-900">{overview.preferred_explanation_style}</p>
          </div>
        </div>
      </section>
      <section className="glass-panel p-6">
        <p className="text-xs uppercase tracking-[0.24em] text-ember">薄弱点</p>
        <div className="mt-4 flex flex-wrap gap-2">
          {overview.weak_concepts.map((concept) => (
            <span key={concept} className="rounded-full border border-black/10 bg-white/55 px-3 py-2 text-sm text-slate-700">
              {concept}
            </span>
          ))}
        </div>
      </section>
      <section className="glass-panel p-6">
        <p className="text-xs uppercase tracking-[0.24em] text-brand">当前记录</p>
        <p className="mt-4 text-sm text-slate-700">
          阅读进度 {paperMemory.progress_percent}% · 上次读到 {paperMemory.last_read_section}
        </p>
        <div className="mt-4 grid gap-4 md:grid-cols-2">
          <div>
            <p className="text-sm text-slate-900">卡点</p>
            <ul className="mt-3 space-y-2 text-sm text-slate-700">
              {paperMemory.stuck_points.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
          <div>
            <p className="text-sm text-slate-900">问题</p>
            <ul className="mt-3 space-y-2 text-sm text-slate-700">
              {paperMemory.key_questions.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
        </div>
      </section>
    </div>
  );
}
