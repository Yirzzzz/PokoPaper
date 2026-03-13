import { AppShell } from "@/components/layout/app-shell";
import { PaperLibraryManager } from "@/features/library/paper-library-manager";
import { fetchPapers } from "@/lib/api/client";

export default async function DexPage() {
  const papers = await fetchPapers();

  return (
    <AppShell showContextPanel={false}>
      <div className="space-y-4">
        <section className="glass-panel bg-hero-grid p-8 shadow-glow">
          <p className="text-xs uppercase tracking-[0.3em] text-brand">Kanto Dex</p>
          <h2 className="mt-3 text-4xl font-semibold text-slate-900">论文图鉴</h2>
        </section>

        <section className="glass-panel p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs uppercase tracking-[0.24em] text-brand">Dex</p>
              <h3 className="mt-2 text-xl font-semibold text-slate-900">已收录论文</h3>
            </div>
          </div>
          <PaperLibraryManager papers={papers} showPokedexControls />
        </section>
      </div>
    </AppShell>
  );
}
