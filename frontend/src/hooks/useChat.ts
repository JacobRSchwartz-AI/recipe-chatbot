import { useState, useCallback } from 'react';
import { Message, ChatState } from '@/lib/types';
import { sendMessage, sendMessageStream } from '@/lib/api';
import { generateId } from '@/lib/utils';

export const useChat = () => {
  const [state, setState] = useState<ChatState>({
    messages: [],
    isLoading: false,
    error: null,
  });

  const addMessage = useCallback((message: Message) => {
    setState(prev => ({
      ...prev,
      messages: [...prev.messages, message],
    }));
  }, []);

  const updateMessage = useCallback((messageId: string, updates: Partial<Message>) => {
    setState(prev => ({
      ...prev,
      messages: prev.messages.map(msg => 
        msg.id === messageId ? { ...msg, ...updates } : msg
      ),
    }));
  }, []);

  const setLoading = useCallback((loading: boolean) => {
    setState(prev => ({ ...prev, isLoading: loading }));
  }, []);

  const setError = useCallback((error: string | null) => {
    setState(prev => ({ ...prev, error }));
  }, []);

  const sendUserMessage = useCallback(async (content: string, useStreaming: boolean = true) => {
    if (!content.trim()) return;

    // Add user message
    const userMessage: Message = {
      id: generateId(),
      content: content.trim(),
      role: 'user',
      timestamp: new Date(),
    };
    addMessage(userMessage);

    // Set loading state
    setLoading(true);
    setError(null);

    if (useStreaming) {
      // Use streaming API
      const assistantMessageId = generateId();
      let assistantContent = '';
      let statusContent = '';
      let currentMetadata: any = {};

      // Add initial assistant message
      const assistantMessage: Message = {
        id: assistantMessageId,
        content: '',
        role: 'assistant',
        timestamp: new Date(),
        isStreaming: true,
        status: 'Processing your request...',
      };
      addMessage(assistantMessage);

      try {
        await sendMessageStream(
          content.trim(),
          // onStatusUpdate
          (status: string) => {
            statusContent = status;
            updateMessage(assistantMessageId, { 
              status,
              isStreaming: true 
            });
          },
          // onToolUpdate
          (tool: string) => {
            statusContent = tool;
            updateMessage(assistantMessageId, { 
              status: tool,
              isStreaming: true 
            });
          },
          // onContentChunk
          (chunk: string) => {
            // Add space between chunks if assistantContent already exists and doesn't end with space
            if (assistantContent && !assistantContent.endsWith(' ') && !chunk.startsWith(' ')) {
              assistantContent += ' ' + chunk;
            } else {
              assistantContent += chunk;
            }
            updateMessage(assistantMessageId, { 
              content: assistantContent,
              status: undefined,
              isStreaming: true 
            });
          },
          // onComplete
          (metadata: any) => {
            currentMetadata = metadata;
            updateMessage(assistantMessageId, { 
              content: assistantContent,
              isStreaming: false,
              status: undefined,
              metadata: {
                tools_used: metadata.tools_used,
                cookware_check: metadata.cookware_check,
                is_cooking_related: metadata.is_cooking_related,
                debug_info: metadata.debug_info,
              },
            });
          },
          // onError
          (error: string) => {
            setError(error);
            updateMessage(assistantMessageId, { 
              content: `Sorry, I encountered an error: ${error}`,
              isStreaming: false,
              status: undefined,
            });
          }
        );
      } catch (error: any) {
        setError(error.message);
        updateMessage(assistantMessageId, { 
          content: `Sorry, I encountered an error: ${error.message}`,
          isStreaming: false,
          status: undefined,
        });
      } finally {
        setLoading(false);
      }
    } else {
      // Use traditional API (fallback)
      try {
        const response = await sendMessage(content.trim());

        const assistantMessage: Message = {
          id: generateId(),
          content: response.response,
          role: 'assistant',
          timestamp: new Date(),
          metadata: {
            tools_used: response.tools_used,
            cookware_check: response.cookware_check,
            is_cooking_related: response.is_cooking_related,
            debug_info: response.debug_info,
          },
        };
        addMessage(assistantMessage);
      } catch (error: any) {
        setError(error.message);
        
        const errorMessage: Message = {
          id: generateId(),
          content: `Sorry, I encountered an error: ${error.message}`,
          role: 'assistant',
          timestamp: new Date(),
        };
        addMessage(errorMessage);
      } finally {
        setLoading(false);
      }
    }
  }, [addMessage, updateMessage, setLoading, setError]);

  return {
    messages: state.messages,
    isLoading: state.isLoading,
    error: state.error,
    sendMessage: sendUserMessage,
    clearError: () => setError(null),
  };
};
