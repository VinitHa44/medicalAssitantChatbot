import { useState, useCallback } from 'react';
import { Message } from '@/lib/types';
import { v4 as uuidv4 } from 'uuid';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

interface Source {
  url: string;
  title?: string;
  score?: number;
}

const getSessionId = (): string => {
  let sessionId = localStorage.getItem('dr_asha_session_id');
  if (!sessionId) {
    sessionId = uuidv4();
    localStorage.setItem('dr_asha_session_id', sessionId);
  }
  return sessionId;
};

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId] = useState(getSessionId);

  const sendTextMessage = useCallback(async (content: string) => {
    if (!content.trim() || isLoading) return;

    const userMessage: Message = {
      id: uuidv4(),
      role: 'user',
      content: content.trim(),
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/api/chat/text`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: content.trim(),
          session_id: sessionId,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      const assistantMessage: Message = {
        id: uuidv4(),
        role: 'assistant',
        content: data.response,
        timestamp: new Date(),
        sources: data.sources?.map((s: Source) => s.url) || [],
        confidence: data.confidence,
        cached: data.cached || false,
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      
      const errorMessage: Message = {
        id: uuidv4(),
        role: 'assistant',
        content: 'I apologize, but I encountered an error processing your request. Please try again or contact support if the issue persists.',
        timestamp: new Date(),
        sources: [],
        confidence: 0,
      };
      
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  }, [isLoading, sessionId]);

  const sendVoiceMessage = useCallback(async (audioBlob: Blob) => {
    if (isLoading) return;

    setIsLoading(true);

    try {
      const formData = new FormData();
      formData.append('audio_file', audioBlob, 'recording.webm');
      formData.append('session_id', sessionId);

      const response = await fetch(`${API_BASE_URL}/api/chat/voice`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      const userMessage: Message = {
        id: uuidv4(),
        role: 'user',
        content: data.transcribed_query,
        timestamp: new Date(),
        isVoice: true,
      };

      setMessages(prev => [...prev, userMessage]);

      const assistantMessage: Message = {
        id: uuidv4(),
        role: 'assistant',
        content: data.response,
        timestamp: new Date(),
        sources: data.sources?.map((s: Source) => s.url) || [],
        confidence: data.confidence,
        isVoice: true,
        audioUrl: data.audio_url ? `${API_BASE_URL}${data.audio_url}` : undefined,
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error processing voice:', error);
      
      const errorMessage: Message = {
        id: uuidv4(),
        role: 'assistant',
        content: 'I apologize, but I encountered an error processing your voice message. Please try again.',
        timestamp: new Date(),
        sources: [],
        confidence: 0,
      };
      
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  }, [isLoading, sessionId]);

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  return {
    messages,
    isLoading,
    sessionId,
    sendTextMessage,
    sendVoiceMessage,
    clearMessages,
  };
}
