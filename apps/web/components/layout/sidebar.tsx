import Link from "next/link";
import { BookOpen, BrainCircuit, MessageSquare } from "lucide-react";

const navItems = [
  { href: "/", label: "图鉴研究所", icon: BookOpen },
  { href: "/chat", label: "问答", icon: MessageSquare },
  { href: "/memory", label: "阅读记忆", icon: BrainCircuit },
];

export function Sidebar() {
  return (
    <aside className="glass-panel flex h-full flex-col gap-6 p-5">
      <div>
        <p className="text-xs uppercase tracking-[0.3em] text-brand">Pokomon</p>
        <h1 className="mt-2 text-2xl font-semibold">Paper Companion Lab</h1>
      </div>
      <nav className="flex flex-col gap-2">
        {navItems.map(({ href, label, icon: Icon }) => (
          <Link
            key={href}
            href={href}
            className="flex items-center gap-3 rounded-2xl border border-white/5 bg-white/5 px-4 py-3 text-sm text-mist transition hover:border-brand/40 hover:bg-white/10 hover:text-white"
          >
            <Icon className="h-4 w-4" />
            {label}
          </Link>
        ))}
      </nav>
    </aside>
  );
}
