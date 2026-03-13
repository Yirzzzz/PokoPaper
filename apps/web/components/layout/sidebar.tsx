import Link from "next/link";
import { BookOpen, BrainCircuit, Library, MessageSquare } from "lucide-react";

const navItems = [
  { href: "/", label: "图鉴研究所", icon: BookOpen },
  { href: "/dex", label: "论文图鉴", icon: Library },
  { href: "/chat", label: "对战记录", icon: MessageSquare },
  { href: "/memory", label: "训练档案", icon: BrainCircuit },
];

export function Sidebar() {
  return (
    <aside className="glass-panel flex h-full flex-col gap-6 p-5">
      <div>
        <p className="text-xs uppercase tracking-[0.3em] text-brand">Pokomon</p>
        <h1 className="mt-2 text-2xl font-semibold text-slate-900">论文图鉴</h1>
      </div>
      <nav className="flex flex-col gap-2">
        {navItems.map(({ href, label, icon: Icon }) => (
          <Link
            key={href}
            href={href}
            className="flex items-center gap-3 rounded-2xl border border-black/10 bg-white/45 px-4 py-3 text-sm text-slate-700 transition hover:border-brand/40 hover:bg-brand/10 hover:text-slate-900"
          >
            <Icon className="h-4 w-4" />
            {label}
          </Link>
        ))}
      </nav>
    </aside>
  );
}
