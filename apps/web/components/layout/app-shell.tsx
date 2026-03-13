import { ReactNode } from "react";

import { ContextPanel } from "@/components/layout/context-panel";
import { Sidebar } from "@/components/layout/sidebar";
import type { Citation } from "@/types";

type AppShellProps = {
  children: ReactNode;
  citations?: Citation[];
  hints?: string[];
  showContextPanel?: boolean;
};

export function AppShell({
  children,
  citations,
  hints,
  showContextPanel = true,
}: AppShellProps) {
  return (
    <div className="min-h-screen p-4 md:p-6">
      <div
        className={`mx-auto grid max-w-[1600px] gap-4 ${
          showContextPanel
            ? "lg:grid-cols-[280px_minmax(0,1fr)] xl:grid-cols-[280px_minmax(0,1fr)_320px]"
            : "lg:grid-cols-[280px_minmax(0,1fr)]"
        }`}
      >
        <Sidebar />
        <main className="min-h-[calc(100vh-3rem)]">{children}</main>
        {showContextPanel ? (
          <div className="lg:col-span-2 xl:col-span-1">
            <ContextPanel citations={citations} hints={hints} />
          </div>
        ) : null}
      </div>
    </div>
  );
}
