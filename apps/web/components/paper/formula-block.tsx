import "katex/dist/katex.min.css";

import ReactMarkdown from "react-markdown";
import rehypeKatex from "rehype-katex";
import remarkMath from "remark-math";

type FormulaBlockProps = {
  latex: string;
  explanation: string;
  variables: Array<{ symbol: string; meaning: string }>;
};

export function FormulaBlock({ latex, explanation, variables }: FormulaBlockProps) {
  const markdown = `$$${latex}$$`;

  return (
    <div className="rounded-3xl border border-black/10 bg-white/55 p-5">
      <div className="prose-katex text-slate-900">
        <ReactMarkdown remarkPlugins={[remarkMath]} rehypePlugins={[rehypeKatex]}>
          {markdown}
        </ReactMarkdown>
      </div>
      <p className="mt-4 text-sm leading-7 text-slate-700">{explanation}</p>
      <div className="mt-4 grid gap-3 md:grid-cols-2">
        {variables.map((variable) => (
          <div key={variable.symbol} className="rounded-2xl bg-white/70 p-3 text-sm text-slate-700">
            <span className="font-semibold text-slate-900">{variable.symbol}</span>: {variable.meaning}
          </div>
        ))}
      </div>
      <button
        type="button"
        className="mt-4 rounded-full border border-brand/30 bg-brand/10 px-4 py-2 text-xs text-brand"
      >
        直观解释
      </button>
    </div>
  );
}
