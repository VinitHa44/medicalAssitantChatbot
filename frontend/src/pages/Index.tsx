import { DisclaimerBanner } from '@/components/DisclaimerBanner';
import { ChatHeader } from '@/components/ChatHeader';
import { ChatMessages } from '@/components/ChatMessages';
import { ChatInput } from '@/components/ChatInput';
import { useChat } from '@/hooks/useChat';
import { Toaster } from '@/components/ui/toaster';
import { Helmet } from 'react-helmet-async';

const Index = () => {
  const { messages, isLoading, sendTextMessage, sendVoiceMessage, clearMessages } = useChat();

  return (
    <>
      <Helmet>
        <title>Dr. Asha - AI Medical Assistant | Health Questions Answered</title>
        <meta name="description" content="Get reliable health information from Dr. Asha, your AI-powered medical assistant. Ask questions about symptoms, conditions, and wellness tips." />
      </Helmet>
      
      <div className="flex min-h-screen flex-col bg-background">
        <DisclaimerBanner />
        <ChatHeader onClearChat={clearMessages} hasMessages={messages.length > 0} />
        
        <main className="flex flex-1 flex-col overflow-hidden">
          <ChatMessages 
            messages={messages} 
            isLoading={isLoading} 
            onSuggestionClick={sendTextMessage}
          />
          <ChatInput
            onSendText={sendTextMessage}
            onSendVoice={sendVoiceMessage}
            isLoading={isLoading}
          />
        </main>
        
        <Toaster />
      </div>
    </>
  );
};

export default Index;
