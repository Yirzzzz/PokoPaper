import { AppShell } from "@/components/layout/app-shell";
import { PaperLibraryManager } from "@/features/library/paper-library-manager";
import { fetchMemoryOverview, fetchPapers } from "@/lib/api/client";
import { UploadPanel } from "@/features/upload/upload-panel";

export default async function HomePage() {
  const [papers, memory] = await Promise.all([fetchPapers(), fetchMemoryOverview()]);

  return (
    <AppShell>
      <div className="space-y-4">
        <section className="glass-panel bg-hero-grid p-8 shadow-glow">
          <div className="flex flex-col gap-6 xl:flex-row xl:items-end xl:justify-between">
            <div>
              <p className="text-xs uppercase tracking-[0.3em] text-brand">图鉴研究所</p>
              <h2 className="mt-3 max-w-3xl text-4xl font-semibold text-white">
                你的论文库
              </h2>
              <p className="mt-4 max-w-2xl text-base leading-8 text-mist">
                上传、整理并继续阅读你关心的论文。
              </p>
            </div>
            <div className="flex flex-wrap gap-3 text-sm text-mist">
              <span className="rounded-full border border-white/10 bg-white/5 px-4 py-2">图鉴：论文库</span>
              <span className="rounded-full border border-white/10 bg-white/5 px-4 py-2">徽章：阅读进度</span>
              <span className="rounded-full border border-white/10 bg-white/5 px-4 py-2">进化链：推荐阅读路径</span>
            </div>
          </div>
        </section>

        <section className="grid gap-4">
          <div className="grid gap-4 xl:grid-cols-[360px_minmax(0,1fr)]">
            <section className="glass-panel p-6">
              <p className="text-xs uppercase tracking-[0.24em] text-ember">阅读徽章</p>
              <div className="mt-4 flex items-end justify-between gap-4">
                <div>
                  <p className="text-5xl font-semibold text-white">{memory.read_papers}</p>
                  <p className="mt-2 text-sm text-mist">累计已读论文</p>
                </div>
                <div className="rounded-3xl border border-white/10 bg-white/5 px-4 py-3 text-right">
                  <p className="text-xs uppercase tracking-[0.24em] text-brand">活跃主题</p>
                  <p className="mt-2 text-sm text-white">{memory.active_topics.length} 个方向</p>
                </div>
              </div>
            </section>

            <section className="glass-panel p-6">
              <div className="flex items-center justify-between">
              <div>
                <p className="text-xs uppercase tracking-[0.24em] text-brand">建议继续阅读</p>
                <h3 className="mt-2 text-xl font-semibold text-white">研究方向</h3>
              </div>
              </div>
              <div className="mt-4 flex flex-wrap gap-2">
                {memory.active_topics.map((topic) => (
                  <span key={topic} className="rounded-full border border-white/10 px-3 py-2 text-sm text-mist">
                    {topic}
                  </span>
                ))}
              </div>
            </section>
          </div>

          <div className="space-y-4">
            <section className="glass-panel p-6">
              <p className="text-xs uppercase tracking-[0.24em] text-brand">上传入口</p>
              <h3 className="mt-2 text-xl font-semibold text-white">上传论文</h3>
              <div className="mt-5">
                <UploadPanel />
              </div>
            </section>
          </div>

          <section className="glass-panel p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs uppercase tracking-[0.24em] text-brand">论文图鉴</p>
                <h3 className="mt-2 text-xl font-semibold text-white">最近加入的论文</h3>
              </div>
            </div>
            <PaperLibraryManager papers={papers} />
          </section>
        </section>
      </div>
    </AppShell>
  );
}
