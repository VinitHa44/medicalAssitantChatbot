import { useState, useRef, useEffect } from 'react';
import { Send, Mic, Square, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { useVoiceRecorder } from '@/hooks/useVoiceRecorder';
import { cn } from '@/lib/utils';
import { toast } from '@/hooks/use-toast';

interface ChatInputProps {
  onSendText: (text: string) => void;
  onSendVoice: (audioBlob: Blob) => void;
  isLoading: boolean;
}

const MAX_CHARS = 500;

export function ChatInput({ onSendText, onSendVoice, isLoading }: ChatInputProps) {
  const [message, setMessage] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const { isRecording, startRecording, stopRecording, error } = useVoiceRecorder();

  const charCount = message.length;
  const isOverLimit = charCount > MAX_CHARS;

  useEffect(() => {
    if (error) {
      toast({
        title: 'Microphone Error',
        description: error,
        variant: 'destructive',
      });
    }
  }, [error]);

  const handleSubmit = () => {
    if (message.trim() && !isLoading && !isOverLimit) {
      onSendText(message);
      setMessage('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleVoiceToggle = async () => {
    if (isRecording) {
      const audioBlob = await stopRecording();
      if (audioBlob && audioBlob.size > 0) {
        // Check size (5MB limit)
        if (audioBlob.size > 5 * 1024 * 1024) {
          toast({
            title: 'Audio too large',
            description: 'Please record a shorter message (max 5MB)',
            variant: 'destructive',
          });
          return;
        }
        onSendVoice(audioBlob);
      }
    } else {
      await startRecording();
    }
  };

  return (
    <div className="border-t border-border bg-card px-4 py-4">
      <div className="container mx-auto max-w-3xl">
        <div className="flex items-end gap-3">
          {/* Voice Button */}
          <Button
            type="button"
            variant={isRecording ? 'destructive' : 'outline'}
            size="icon"
            onClick={handleVoiceToggle}
            disabled={isLoading}
            className={cn(
              'relative h-11 w-11 flex-shrink-0 rounded-full transition-all',
              isRecording && 'animate-pulse'
            )}
            aria-label={isRecording ? 'Stop recording' : 'Start recording'}
          >
            {isRecording ? (
              <>
                <Square className="h-4 w-4" />
                <span className="absolute -top-1 -right-1 flex h-3 w-3">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-destructive opacity-75" />
                  <span className="relative inline-flex h-3 w-3 rounded-full bg-destructive" />
                </span>
              </>
            ) : (
              <Mic className="h-5 w-5" />
            )}
          </Button>

          {/* Text Input */}
          <div className="relative flex-1">
            <Textarea
              ref={textareaRef}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={isRecording ? 'Recording...' : 'Ask Dr. Asha a question...'}
              disabled={isLoading || isRecording}
              className={cn(
                'min-h-[44px] max-h-32 resize-none pr-12 rounded-2xl',
                isOverLimit && 'border-destructive focus-visible:ring-destructive'
              )}
              rows={1}
            />
            <span
              className={cn(
                'absolute bottom-2 right-3 text-xs',
                isOverLimit ? 'text-destructive' : 'text-muted-foreground'
              )}
            >
              {charCount}/{MAX_CHARS}
            </span>
          </div>

          {/* Send Button */}
          <Button
            type="button"
            onClick={handleSubmit}
            disabled={!message.trim() || isLoading || isOverLimit || isRecording}
            size="icon"
            className="h-11 w-11 flex-shrink-0 rounded-full"
          >
            {isLoading ? (
              <Loader2 className="h-5 w-5 animate-spin" />
            ) : (
              <Send className="h-5 w-5" />
            )}
          </Button>
        </div>

        {isRecording && (
          <p className="mt-2 text-center text-sm text-muted-foreground animate-pulse">
            🎙️ Recording... Click the stop button when done
          </p>
        )}
      </div>
    </div>
  );
}
