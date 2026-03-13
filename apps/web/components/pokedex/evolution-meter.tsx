type EvolutionMeterProps = {
  progress: number;
  label: string;
};

export function EvolutionMeter({ progress, label }: EvolutionMeterProps) {
  const clamped = Math.max(0, Math.min(100, progress));

  return (
    <div className="rounded-3xl border border-black/10 bg-white/55 p-4">
      <div className="flex items-center justify-between gap-4">
        <p className="text-sm text-slate-700">{label}</p>
        <p className="text-sm font-medium text-slate-900">{clamped}%</p>
      </div>
      <div className="mt-3 h-3 overflow-hidden rounded-full bg-black/10">
        <div
          className="h-full rounded-full bg-gradient-to-r from-brand via-emerald-300 to-sky-300 transition-all"
          style={{ width: `${clamped}%` }}
        />
      </div>
      <div className="mt-3 flex justify-between text-[11px] uppercase tracking-[0.2em] text-slate-600">
        <span>初始</span>
        <span>进化</span>
        <span>掌握</span>
      </div>
    </div>
  );
}
