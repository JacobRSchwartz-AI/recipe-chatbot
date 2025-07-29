'use client';

import { useEffect, useRef } from 'react';
import { useChat } from '@/hooks/useChat';
import MessageBubble from './MessageBubble';
import ChatInput from './ChatInput';
import LoadingIndicator from './LoadingIndicator';

export default function ChatContainer() {
  const { messages, isLoading, error, sendMessage, clearError } = useChat();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b px-4 py-3 shadow-sm">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-xl font-semibold text-gray-800">Recipe Chatbot</h1>
          <p className="text-sm text-gray-600">Ask me about cooking, recipes, or what you can make with your ingredients!</p>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto px-4 py-4">
        <div className="max-w-4xl mx-auto">
          {/* Welcome message */}
          {messages.length === 0 && (
            <div className="text-center py-8">
              <div className="bg-blue-50 rounded-lg p-6 mb-4">
                <h2 className="text-lg font-semibold text-blue-800 mb-2">Welcome to Recipe Chatbot! 👨‍🍳</h2>
                <p className="text-blue-600">I can help you with:</p>
                <ul className="text-blue-600 text-left mt-2 space-y-1">
                  <li>• Finding recipes for specific dishes</li>
                  <li>• Suggesting what to cook with your ingredients</li>
                  <li>• Checking if you have the right cookware</li>
                  <li>• General cooking tips and techniques</li>
                </ul>
                <p className="text-blue-600 mt-3 font-medium">Try asking: "What can I make with chicken and rice?" or "How do I make scrambled eggs?"</p>
              </div>
            </div>
          )}

          {/* Error Display */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
              <div className="flex justify-between items-center">
                <div className="text-red-700">
                  <strong>Error:</strong> {error}
                </div>
                <button
                  onClick={clearError}
                  className="text-red-500 hover:text-red-700 text-sm underline"
                >
                  Dismiss
                </button>
              </div>
            </div>
          )}

          {/* Messages */}
          {messages.map((message) => (
            <MessageBubble key={message.id} message={message} />
          ))}

          {/* Loading Indicator - only show if loading and no streaming messages */}
          {isLoading && !messages.some(msg => msg.isStreaming) && <LoadingIndicator />}

          {/* Scroll anchor */}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Area */}
      <ChatInput onSendMessage={sendMessage} isLoading={isLoading} />
    </div>
  );
}
