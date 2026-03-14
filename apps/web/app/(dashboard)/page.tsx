import { AppShell } from "@/components/layout/app-shell";
import Link from "next/link";
import { fetchMemoryOverview, fetchPapers } from "@/lib/api/client";
import { UploadPanel } from "@/features/upload/upload-panel";

export default async function HomePage() {
  const [papers, memory] = await Promise.all([fetchPapers(), fetchMemoryOverview()]);

  return (
    <AppShell showContextPanel={false}>
      <div className="space-y-4">
        <section className="glass-panel bg-hero-grid p-8 shadow-glow">
          <div className="flex flex-col gap-6 xl:flex-row xl:items-end xl:justify-between">
            <div>
              <p className="text-xs uppercase tracking-[0.3em] text-brand">Research Lab</p>
              <h2 className="mt-3 max-w-3xl text-4xl font-semibold text-slate-900">图鉴研究所</h2>
            </div>
            <div className="flex flex-wrap gap-3 text-sm text-slate-700">
              <span className="rounded-full border border-black/10 bg-white/60 px-4 py-2">151 图鉴</span>
              <span className="rounded-full border border-black/10 bg-white/60 px-4 py-2">像素卡</span>
              <span className="rounded-full border border-black/10 bg-white/60 px-4 py-2">训练线</span>
            </div>
          </div>
        </section>

        <section className="grid gap-4">
          <div className="grid gap-4 xl:grid-cols-[360px_minmax(0,1fr)]">
            <section className="glass-panel p-6">
              <p className="text-xs uppercase tracking-[0.24em] text-ember">阅读徽章</p>
              <div className="mt-4 flex items-end justify-between gap-4">
                <div>
                  <p className="text-5xl font-semibold text-slate-900">{memory.read_papers}</p>
                  <p className="mt-2 text-sm text-slate-700">已读论文</p>
                </div>
                <div className="rounded-3xl border border-black/10 bg-white/55 px-4 py-3 text-right">
                  <p className="text-xs uppercase tracking-[0.24em] text-brand">活跃主题</p>
                  <p className="mt-2 text-sm font-medium text-slate-900">{memory.active_topics.length} 个方向</p>
                </div>
              </div>
            </section>

            <section className="glass-panel p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs uppercase tracking-[0.24em] text-brand">方向</p>
                  <h3 className="mt-2 text-xl font-semibold text-slate-900">属性</h3>
                </div>
              </div>
              {memory.active_topics.length > 0 ? (
                <div className="mt-4 flex flex-wrap gap-2">
                  {memory.active_topics.map((topic) => (
                    <span
                      key={topic}
                      className="rounded-full border border-black/10 bg-white/60 px-3 py-2 text-sm font-medium text-slate-800"
                    >
                      {topic}
                    </span>
                  ))}
                </div>
              ) : (
                <p className="mt-4 text-sm text-slate-700">收录带标签的论文后会出现在这里。</p>
              )}
            </section>
          </div>

          <div className="space-y-4">
            <section className="glass-panel p-6">
              <p className="text-xs uppercase tracking-[0.24em] text-brand">收录</p>
              <h3 className="mt-2 text-xl font-semibold text-slate-900">上传论文</h3>
              <div className="mt-5">
                <UploadPanel />
              </div>
            </section>
          </div>

          <section className="glass-panel p-6">
            <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
              <div>
                <p className="text-xs uppercase tracking-[0.24em] text-brand">论文图鉴</p>
                <h3 className="mt-2 text-xl font-semibold text-slate-900">前往 Kanto Paper Dex</h3>
                <p className="mt-3 text-sm font-medium text-slate-800">已收录 {papers.length} 篇</p>
              </div>
              <Link
                href="/dex"
                className="inline-flex rounded-full border border-black/10 bg-white/60 px-5 py-3 text-sm font-medium text-slate-900 transition hover:bg-white/80"
              >
                打开论文图鉴
              </Link>
            </div>
          </section>
        </section>
      </div>
    </AppShell>
  );
}
