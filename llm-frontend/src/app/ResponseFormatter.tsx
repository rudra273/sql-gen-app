"use client";

import type React from "react";
import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { atomDark } from "react-syntax-highlighter/dist/esm/styles/prism";
import { Check, Copy, Code } from "lucide-react";
import { motion } from "framer-motion";

interface ResponseFormatterProps {
  content: string;
}

const ResponseFormatter: React.FC<ResponseFormatterProps> = ({ content }) => {
  const [copyStatus, setCopyStatus] = useState<Record<number, boolean>>({});

  const handleCopy = async (text: string, blockId: number) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopyStatus((prev) => ({ ...prev, [blockId]: true }));
      setTimeout(() => {
        setCopyStatus((prev) => ({ ...prev, [blockId]: false }));
      }, 2000);
    } catch (err) {
      console.error("Failed to copy:", err);
    }
  };

  return (
    <div className="space-y-6 w-full max-w-4xl text-white p-6 bg-[#202020] rounded-xl shadow-2xl">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          code({ node, inline, className, children, ...props }) {
            const match = /language-(\w+)/.exec(className || "");
            const codeContent = String(children).trim();
            const blockId = node?.position?.start?.line ?? Math.random();

            return !inline ? (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
                className="relative bg-[#303030] rounded-lg p-4 shadow-lg overflow-hidden"
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    <Code className="w-5 h-5 text-white/60" />
                    <span className="text-sm font-semibold text-white/60">
                      {match?.[1] || "plaintext"}
                    </span>
                  </div>
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => handleCopy(codeContent, blockId)}
                    className="p-1.5 bg-[#404040] rounded-md hover:bg-[#505050] transition-colors duration-200"
                  >
                    {copyStatus[blockId] ? (
                      <Check className="w-4 h-4 text-green-400" />
                    ) : (
                      <Copy className="w-4 h-4 text-white/60" />
                    )}
                  </motion.button>
                </div>
                <SyntaxHighlighter
                  style={atomDark}
                  language={match?.[1] || "plaintext"}
                  PreTag="pre"
                  customStyle={{
                    background: "transparent",
                    padding: 0,
                    margin: 0,
                    fontSize: "0.9rem",
                  }}
                  {...props}
                >
                  {codeContent}
                </SyntaxHighlighter>
              </motion.div>
            ) : (
              <code className="bg-[#303030] text-green-400 px-1.5 py-0.5 rounded-md font-mono text-sm">
                {children}
              </code>
            );
          },
          p: (props) => <p className="text-white leading-relaxed" {...props} />,
          h1: (props) => (
            <h1 className="text-3xl font-bold text-white mb-4" {...props} />
          ),
          h2: (props) => (
            <h2 className="text-2xl font-semibold text-white mb-3" {...props} />
          ),
          h3: (props) => (
            <h3 className="text-xl font-semibold text-white mb-2" {...props} />
          ),
          ul: (props) => (
            <ul className="list-disc list-inside space-y-1 ml-4" {...props} />
          ),
          ol: (props) => (
            <ol
              className="list-decimal list-inside space-y-1 ml-4"
              {...props}
            />
          ),
          li: (props) => <li className="text-white" {...props} />,
          a: (props) => (
            <a
              className="text-blue-400 hover:text-blue-300 underline transition-colors duration-200"
              {...props}
            />
          ),
          blockquote: (props) => (
            <blockquote
              className="border-l-4 border-[#404040] pl-4 italic text-white/60"
              {...props}
            />
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
};

export default ResponseFormatter;
