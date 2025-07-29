import { JSX } from 'react';
import Markdown from 'react-markdown';

/**
 * A custom markdown component that takes in a string and returns a markdown component
 * using Tailwind CSS classes.
 * @param {children.string} children - The markdown content to render
 * @param {isInChatBubble} isInChatBubble - Whether this is being rendered inside a chat bubble
 * @returns {JSX.Element} The rendered markdown component
 */
export default function MarkdownMessage({ 
  children, 
  isInChatBubble = false 
}: { 
  children: string | null | undefined;
  isInChatBubble?: boolean;
}): JSX.Element {
  const textClasses = isInChatBubble ? "text-gray-900" : "text-slate-700 dark:text-white";
  const headingClasses = isInChatBubble ? "text-gray-900" : "text-slate-800 dark:text-white";
  const codeClasses = isInChatBubble ? "bg-white bg-opacity-60 text-gray-800" : "bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-100";
  const preClasses = isInChatBubble ? "bg-white bg-opacity-60 text-gray-800" : "bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-100";
  
  return (
    <Markdown
      components={{
        p: ({ children }: any) => <p className={`${textClasses} mb-2`}>{children}</p>,
        h1: ({ children }: any) => <h1 className={`text-2xl font-bold ${headingClasses} mb-4 mt-6`}>{children}</h1>,
        h2: ({ children }: any) => <h2 className={`text-xl font-bold ${headingClasses} mb-3 mt-5`}>{children}</h2>,
        h3: ({ children }: any) => <h3 className={`text-lg font-bold ${headingClasses} mb-2 mt-4`}>{children}</h3>,
        h4: ({ children }: any) => <h4 className={`text-base font-bold ${headingClasses} mb-2 mt-3`}>{children}</h4>,
        ul: ({ children }: any) => <ul className={`list-disc pl-6 ${textClasses} mb-2`}>{children}</ul>,
        ol: ({ children }: any) => <ol className={`list-decimal pl-6 ${textClasses} mb-2`}>{children}</ol>,
        li: ({ children }: any) => <li className={`mb-1 ${textClasses}`}>{children}</li>,
        code: ({ children }: any) => <code className={`${codeClasses} p-1 rounded-sm font-mono text-sm`}>{children}</code>,
        pre: ({ children }: any) => <pre className={`${preClasses} p-4 rounded-md font-mono text-sm overflow-x-auto mb-4`}>{children}</pre>,
        blockquote: ({ children }: any) => <blockquote className={`border-l-4 border-gray-400 pl-4 italic ${textClasses} opacity-80 my-4`}>{children}</blockquote>,
        strong: ({ children }: any) => <strong className={`font-bold ${headingClasses}`}>{children}</strong>,
        em: ({ children }: any) => <em className={`italic ${textClasses}`}>{children}</em>,
        a: ({ children, href }: any) => (
          <a className="text-blue-600 hover:text-blue-800 hover:underline" href={href as string}>
            {children}
          </a>
        ),
        hr: () => <hr className="border-gray-400 my-4" />,
      }}
    >
      {children}
    </Markdown>
  );
}
