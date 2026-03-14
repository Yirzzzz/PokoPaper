"use client";

import { useEffect } from "react";

import { useAppStore } from "@/store/app-store";

export function ActivePaperSync({ paperId }: { paperId: string }) {
  const setActivePaperId = useAppStore((state) => state.setActivePaperId);

  useEffect(() => {
    setActivePaperId(paperId);
  }, [paperId, setActivePaperId]);

  return null;
}
