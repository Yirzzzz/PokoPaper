import type { MemoryOverview, ReadingMemory } from "@/types";

type MemoryPanelProps = {
  overview: MemoryOverview;
  paperMemory: ReadingMemory;
};

export function MemoryPanel({ overview, paperMemory }: MemoryPanelProps) {
  return (
    <div className="grid gap-4">
      <section className="glass-panel p-6">
        <p className="text-xs uppercase tracking-[0.24em] text-brand">用户画像</p>
        <div className="mt-4 grid gap-4 md:grid-cols-2">
          <div>
            <p className="text-sm text-mist">已读论文</p>
            <p className="mt-2 text-3xl font-semibold text-white">{overview.read_papers}</p>
          </div>
          <div>
            <p className="text-sm text-mist">解释偏好</p>
            <p className="mt-2 text-lg text-white">{overview.preferred_explanation_style}</p>
          </div>
        </div>
      </section>
      <section className="glass-panel p-6">
        <p className="text-xs uppercase tracking-[0.24em] text-ember">薄弱知识点</p>
        <div className="mt-4 flex flex-wrap gap-2">
          {overview.weak_concepts.map((concept) => (
            <span key={concept} className="rounded-full border border-white/10 px-3 py-2 text-sm text-mist">
              {concept}
            </span>
          ))}
        </div>
      </section>
      <section className="glass-panel p-6">
        <p className="text-xs uppercase tracking-[0.24em] text-brand">当前论文记忆</p>
        <p className="mt-4 text-sm text-mist">
          阅读进度 {paperMemory.progress_percent}% · 上次读到 {paperMemory.last_read_section}
        </p>
        <div className="mt-4 grid gap-4 md:grid-cols-2">
          <div>
            <p className="text-sm text-white">卡住的点</p>
            <ul className="mt-3 space-y-2 text-sm text-mist">
              {paperMemory.stuck_points.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
          <div>
            <p className="text-sm text-white">关键问题</p>
            <ul className="mt-3 space-y-2 text-sm text-mist">
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
