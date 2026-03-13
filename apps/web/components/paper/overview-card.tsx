import type { ReactNode } from "react";

type OverviewCardProps = {
  eyebrow: string;
  title: string;
  children: ReactNode;
};

export function OverviewCard({ eyebrow, title, children }: OverviewCardProps) {
  return (
    <section className="glass-panel p-6">
      <p className="text-xs uppercase tracking-[0.24em] text-brand">{eyebrow}</p>
      <h3 className="mt-2 text-xl font-semibold text-slate-900">{title}</h3>
      <div className="mt-4 text-sm leading-7 text-slate-700">{children}</div>
    </section>
  );
}
