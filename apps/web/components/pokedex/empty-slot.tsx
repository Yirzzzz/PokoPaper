type EmptySlotProps = {
  eyebrow: string;
  title: string;
  description: string;
};

export function EmptySlot({ eyebrow, title, description }: EmptySlotProps) {
  return (
    <section className="glass-panel border border-dashed border-black/10 p-8 text-center">
      <p className="text-xs uppercase tracking-[0.28em] text-brand">{eyebrow}</p>
      <h3 className="mt-3 text-2xl font-semibold text-slate-900">{title}</h3>
      <div className="mx-auto mt-6 grid h-28 w-28 place-items-center rounded-[2rem] border border-black/10 bg-white/55">
        <div className="h-16 w-16 rounded-full border border-brand/30 bg-brand/10" />
      </div>
      <p className="mx-auto mt-6 max-w-md text-sm leading-7 text-slate-700">{description}</p>
    </section>
  );
}
