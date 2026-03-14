import { AppShell } from "@/components/layout/app-shell";

export default function MemoryLabPage() {
  return (
    <AppShell showContextPanel={false}>
      <section className="glass-panel p-6 text-sm text-slate-700">
        Memory Lab 已从当前稳定版本主链路中停用。
      </section>
    </AppShell>
  );
}
