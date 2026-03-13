import type { Citation } from "@/types";

type ContextPanelProps = {
  citations?: Citation[];
  hints?: string[];
};

export function ContextPanel({ citations = [], hints = [] }: ContextPanelProps) {
  return (
    <aside className="glass-panel flex h-full flex-col gap-5 p-5 xl:sticky xl:top-6">
      <section>
        <p className="text-xs uppercase tracking-[0.24em] text-brand">引用来源</p>
        <div className="mt-3 space-y-3">
          {citations.length === 0 ? (
            <p className="text-sm text-mist">当前还没有引用片段。</p>
          ) : (
            citations.map((citation, index) => (
              <div key={`${citation.chunk_id}-${index}`} className="rounded-3xl border border-white/10 bg-white/5 p-4">
                <p className="text-sm font-medium text-white">{citation.section_title}</p>
                <p className="mt-1 text-xs text-mist">
                  Page {citation.page_num} · {citation.support_level}
                </p>
              </div>
            ))
          )}
        </div>
      </section>
      <section>
        <p className="text-xs uppercase tracking-[0.24em] text-ember">背景建议</p>
        <div className="mt-3 space-y-3">
          {hints.length === 0 ? (
            <p className="text-sm text-mist">没有额外背景建议。</p>
          ) : (
            hints.map((hint) => (
              <div key={hint} className="rounded-3xl border border-white/10 bg-white/5 p-4 text-sm text-mist">
                {hint}
              </div>
            ))
          )}
        </div>
      </section>
    </aside>
  );
}
