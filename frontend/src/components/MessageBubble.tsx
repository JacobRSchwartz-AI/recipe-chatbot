import { Message } from '@/lib/types';
import { formatTime, cn } from '@/lib/utils';

interface MessageBubbleProps {
  message: Message;
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user';
  
  return (
    <div className={cn('flex w-full mb-4', isUser ? 'justify-end' : 'justify-start')}>
      <div className={cn('max-w-[80%] rounded-lg px-4 py-2', {
        'bg-blue-500 text-white': isUser,
        'bg-gray-100 text-gray-900': !isUser,
      })}>
        {/* Show streaming status for assistant messages */}
        {!isUser && message.isStreaming && message.status && (
          <div className="text-sm text-gray-600 italic mb-2 flex items-center">
            <div className="animate-pulse w-2 h-2 bg-blue-500 rounded-full mr-2"></div>
            {message.status}
          </div>
        )}
        
        <div className="whitespace-pre-wrap break-words">
          {message.content}
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
