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
    <div className="rounded-3xl border border-white/10 bg-black/20 p-5">
      <div className="prose-katex text-white">
        <ReactMarkdown remarkPlugins={[remarkMath]} rehypePlugins={[rehypeKatex]}>
          {markdown}
        </ReactMarkdown>
      </div>
      <p className="mt-4 text-sm leading-7 text-mist">{explanation}</p>
      <div className="mt-4 grid gap-3 md:grid-cols-2">
        {variables.map((variable) => (
          <div key={variable.symbol} className="rounded-2xl bg-white/5 p-3 text-sm text-mist">
            <span className="font-semibold text-white">{variable.symbol}</span>: {variable.meaning}
          </div>
        ))}
      </div>
      <button
        type="button"
        className="mt-4 rounded-full border border-brand/30 bg-brand/10 px-4 py-2 text-xs text-brand"
      >
        TODO: 把公式翻译成直观语言
      </button>
    </div>
  );
}
