import { useState, useCallback } from 'react';
import { Message, ChatState } from '@/lib/types';
import { sendMessage } from '@/lib/api';
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

  const setLoading = useCallback((loading: boolean) => {
    setState(prev => ({ ...prev, isLoading: loading }));
  }, []);

  const setError = useCallback((error: string | null) => {
    setState(prev => ({ ...prev, error }));
  }, []);

  const sendUserMessage = useCallback(async (content: string) => {
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

    try {
      // Call API
      const response = await sendMessage(content.trim());

      // Add assistant response
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
      
      // Add error message from assistant
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
  }, [addMessage, setLoading, setError]);

  return {
    messages: state.messages,
    isLoading: state.isLoading,
    error: state.error,
    sendMessage: sendUserMessage,
    clearError: () => setError(null),
  };
};
