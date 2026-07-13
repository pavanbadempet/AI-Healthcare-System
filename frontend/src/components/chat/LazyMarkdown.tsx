/**
 * LazyMarkdown — Dynamically imports react-markdown + remark-gfm.
 * Keeps the ~120KB unified/micromark ecosystem out of Chat's initial chunk.
 */
import { lazy, Suspense, memo } from "react";

const ReactMarkdown = lazy(() => import("react-markdown"));

// remark-gfm is loaded alongside react-markdown
let remarkGfmPlugin: any[] = [];
import("remark-gfm").then((mod) => {
  remarkGfmPlugin = [mod.default];
});

interface LazyMarkdownProps {
  children: string;
  className?: string;
}

function MarkdownFallback({ children }: { children: string }) {
  return (
    <pre className="whitespace-pre-wrap font-mono text-[11px] uppercase leading-relaxed">
      {children}
    </pre>
  );
}

function LazyMarkdownInner({ children, className }: LazyMarkdownProps) {
  return (
    <Suspense fallback={<MarkdownFallback>{children}</MarkdownFallback>}>
      <ReactMarkdown remarkPlugins={remarkGfmPlugin}>
        {children}
      </ReactMarkdown>
    </Suspense>
  );
}

export default memo(LazyMarkdownInner);
