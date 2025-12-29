import { Message } from '@/lib/types';
import { MessageBubble } from './MessageBubble';
import { TypingIndicator } from './TypingIndicator';
import { WelcomeMessage } from './WelcomeMessage';
import { useRef, useEffect } from 'react';

interface ChatMessagesProps {
  messages: Message[];
  isLoading: boolean;
  onSuggestionClick?: (text: string) => void;
}

export function ChatMessages({ messages, isLoading, onSuggestionClick }: ChatMessagesProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6">
      <div className="container mx-auto max-w-3xl space-y-4">
        {messages.length === 0 && !isLoading && (
          <WelcomeMessage onSuggestionClick={onSuggestionClick} />
        )}
        
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}
        
        {isLoading && <TypingIndicator />}
        
        <div ref={messagesEndRef} />
      </div>
    </div>
  );
}
