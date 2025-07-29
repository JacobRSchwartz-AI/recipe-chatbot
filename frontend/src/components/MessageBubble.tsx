import { useState } from 'react';
import { Message } from '@/lib/types';
import { formatTime, cn } from '@/lib/utils';
import MarkdownMessage from './MarkdownMessage';
import AnimatedDots from './AnimatedDots';
import { CopyIcon, CheckIcon } from '@radix-ui/react-icons';

interface MessageBubbleProps {
  message: Message;
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user';
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(message.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000); // Reset after 2 seconds
    } catch (err) {
      console.error('Failed to copy text: ', err);
    }
  };
  
  return (
    <div className={cn('flex w-full mb-4', isUser ? 'justify-end' : 'justify-start')}>
      <div className={cn('max-w-[80%] rounded-lg px-4 py-2 relative group', {
        'bg-blue-500 text-white': isUser,
        'bg-gray-100 text-gray-900': !isUser,
      })}>
        {/* Copy button for assistant messages */}
        {!isUser && message.content && (
          <button
            onClick={handleCopy}
            className="absolute top-2 right-2 p-1 rounded hover:bg-gray-200 hover:bg-opacity-80 transition-colors duration-200 opacity-0 group-hover:opacity-100"
            title={copied ? 'Copied!' : 'Copy message'}
          >
            {copied ? (
              <CheckIcon className="w-4 h-4 text-green-600" />
            ) : (
              <CopyIcon className="w-4 h-4 text-gray-600" />
            )}
          </button>
        )}
        
        {/* Show streaming status for assistant messages */}
        {!isUser && message.isStreaming && message.status && (
          <div className="text-sm text-gray-600 italic mb-2 flex items-center">
            <div className="animate-pulse w-2 h-2 bg-blue-500 rounded-full mr-2"></div>
            {message.status.endsWith('...') ? (
              <>
                {message.status.slice(0, -3)}
                <AnimatedDots />
              </>
            ) : (
              message.status
            )}
          </div>
        )}
        
        <div className={cn("whitespace-pre-wrap break-words", {
          "pr-8": !isUser && message.content, // Add right padding for copy button
        })}>
          {/* Use MarkdownMessage for assistant messages, plain text for user messages */}
          {isUser ? (
            message.content
          ) : (
            <MarkdownMessage isInChatBubble={true}>{message.content}</MarkdownMessage>
          )}
          {!isUser && message.isStreaming && !message.status && (
            <span className="inline-block w-2 h-4 bg-gray-400 animate-pulse ml-1"></span>
          )}
        </div>
        
        {/* Show metadata for assistant messages */}
        {!isUser && message.metadata && !message.isStreaming && (
          <div className="mt-2 pt-2 border-t border-gray-200 text-xs text-gray-600">
            {message.metadata.tools_used && message.metadata.tools_used.length > 0 && (
              <div className="mb-1">
                <span className="font-semibold">Tools used:</span> {message.metadata.tools_used.join(', ')}
              </div>
            )}
            {message.metadata.is_cooking_related !== undefined && (
              <div className="mb-1">
                <span className="font-semibold">Cooking related:</span> {message.metadata.is_cooking_related ? 'Yes' : 'No'}
              </div>
            )}
            {message.metadata.cookware_check && (
              <div className="mb-1">
                <span className="font-semibold">Cookware check:</span> {JSON.stringify(message.metadata.cookware_check, null, 2)}
              </div>
            )}
          </div>
        )}
        
        <div className={cn('text-xs mt-1 opacity-70', {
          'text-blue-100': isUser,
          'text-gray-500': !isUser,
        })}>
          {formatTime(message.timestamp)}
        </div>
      </div>
    </div>
  );
}
