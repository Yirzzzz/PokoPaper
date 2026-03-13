"use client";

import { useEffect, useState, useTransition } from "react";
import { useRouter } from "next/navigation";

import { fetchIngestionJob } from "@/lib/api/client";

type UploadState =
  | { status: "idle" }
  | { status: "uploading" }
  | { status: "processing"; paperId: string; jobId: string; progress: number; stage: string }
  | { status: "done"; paperId: string; jobId: string }
  | { status: "error"; message: string };

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

export function UploadPanel() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [state, setState] = useState<UploadState>({ status: "idle" });
  const [isPending, startTransition] = useTransition();

  useEffect(() => {
    if (state.status !== "processing") {
      return;
    }
    let cancelled = false;
    const timer = window.setInterval(async () => {
      try {
        const job = await fetchIngestionJob(state.jobId);
        if (cancelled) return;
        if (job.status === "completed") {
          window.clearInterval(timer);
          setState({ status: "done", paperId: job.paper_id, jobId: job.job_id });
          router.push(`/papers/${job.paper_id}`);
          router.refresh();
          return;
        }
        setState({
          status: "processing",
          paperId: job.paper_id,
          jobId: job.job_id,
          progress: job.progress,
          stage: job.stage,
        });
      } catch (error) {
        if (cancelled) return;
        window.clearInterval(timer);
        setState({
          status: "error",
          message: error instanceof Error ? error.message : "polling failed",
        });
      }
    }, 1200);

    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [router, state]);

  return (
    <div className="rounded-3xl border border-white/10 bg-black/20 p-5">
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-white">上传新论文</p>
          <p className="mt-1 text-sm text-mist">选择 PDF 开始解析。</p>
        </div>
      </div>
      <input
        type="file"
        accept="application/pdf"
        onChange={(event) => setFile(event.target.files?.[0] ?? null)}
        className="mt-4 block w-full text-sm text-mist file:mr-4 file:rounded-full file:border-0 file:bg-brand file:px-4 file:py-2 file:text-sm file:font-medium file:text-black"
      />
      <button
        type="button"
        disabled={!file || isPending}
        onClick={() =>
          startTransition(async () => {
            if (!file) return;
            setState({ status: "uploading" });
            try {
              const formData = new FormData();
              formData.append("file", file);
              const response = await fetch(`${API_BASE_URL}/papers/upload`, {
                method: "POST",
                body: formData,
              });
              if (!response.ok) {
                throw new Error("upload failed");
              }
              const data = (await response.json()) as { paper_id: string; job_id: string };
              setState({
                status: "processing",
                paperId: data.paper_id,
                jobId: data.job_id,
                progress: 10,
                stage: "uploaded",
              });
            } catch (error) {
              setState({
                status: "error",
                message: error instanceof Error ? error.message : "unknown error",
              });
            }
          })
        }
        className="mt-4 rounded-full bg-brand px-4 py-2 text-sm font-medium text-black disabled:cursor-not-allowed disabled:opacity-40"
      >
        {isPending ? "上传中..." : "开始解析"}
      </button>
      <div className="mt-4 text-sm text-mist">
        {state.status === "idle" ? "选择 PDF 后开始解析。"
          : null}
        {state.status === "uploading" ? "正在上传..."
          : null}
        {state.status === "processing"
          ? `正在解析中：${state.stage} · ${state.progress}%`
          : null}
        {state.status === "done" ? "解析完成，正在进入论文页。"
          : null}
        {state.status === "error" ? `上传失败：${state.message}`
          : null}
      </div>
    </div>
  );
}
