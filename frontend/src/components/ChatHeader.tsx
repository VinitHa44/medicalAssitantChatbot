import { Stethoscope, RotateCcw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import drAshaAvatar from '@/assets/dr-asha-avatar.png';

interface ChatHeaderProps {
  onClearChat: () => void;
  hasMessages: boolean;
}

export function ChatHeader({ onClearChat, hasMessages }: ChatHeaderProps) {
  return (
    <header className="border-b border-border bg-card px-4 py-4 shadow-sm">
      <div className="container mx-auto flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="relative">
            <img 
              src={drAshaAvatar} 
              alt="Dr. Asha" 
              className="h-12 w-12 rounded-full border-2 border-primary/20 object-cover"
            />
            <div className="absolute -bottom-0.5 -right-0.5 h-3.5 w-3.5 rounded-full border-2 border-card bg-success" />
          </div>
          <div>
            <h1 className="flex items-center gap-2 text-xl font-semibold text-foreground">
              <Stethoscope className="h-5 w-5 text-primary" />
              Dr. Asha
            </h1>
            <p className="text-sm text-muted-foreground">Medical Assistant</p>
          </div>
        </div>
        
        {hasMessages && (
          <Button
            variant="outline"
            size="sm"
            onClick={onClearChat}
            className="gap-2"
          >
            <RotateCcw className="h-4 w-4" />
            New Chat
          </Button>
        )}
      </div>
    </header>
  );
}
