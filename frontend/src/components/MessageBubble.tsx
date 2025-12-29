import { Message } from '@/lib/types';
import { User, Zap, AlertTriangle, ExternalLink, Mic, Volume2, Pause, RotateCcw } from 'lucide-react';
import drAshaAvatar from '@/assets/dr-asha-avatar.png';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { useState, useRef } from 'react';

interface MessageBubbleProps {
  message: Message;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user';
  const isLowConfidence = message.confidence !== undefined && message.confidence < 0.7;
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const playAudio = () => {
    if (!message.audioUrl) return;
    
    if (!audioRef.current) {
      audioRef.current = new Audio(message.audioUrl);
      audioRef.current.onended = () => setIsPlayingAudio(false);
      audioRef.current.onerror = () => {
        setIsPlayingAudio(false);
        console.error('Error playing audio');
      };
    }
    
    audioRef.current.play().catch((err) => {
      console.error('Error playing audio:', err);
      setIsPlayingAudio(false);
    });
    setIsPlayingAudio(true);
  };

  const pauseAudio = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      setIsPlayingAudio(false);
    }
  };

  const restartAudio = () => {
    if (audioRef.current) {
      audioRef.current.currentTime = 0;
      audioRef.current.play();
      setIsPlayingAudio(true);
    }
  };

  return (
    <div
      className={cn(
        'flex gap-3 animate-fade-in-up',
        isUser ? 'flex-row-reverse' : 'flex-row'
      )}
    >
      {/* Avatar */}
      <div className="flex-shrink-0">
        {isUser ? (
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary">
            <User className="h-5 w-5 text-primary-foreground" />
          </div>
        ) : (
          <img
            src={drAshaAvatar}
            alt="Dr. Asha"
            className="h-10 w-10 rounded-full border border-border object-cover"
          />
        )}
      </div>

      {/* Message content */}
      <div className="flex flex-col gap-2 flex-1 min-w-0">
        <div
          className={cn(
            'rounded-2xl px-4 py-3 max-w-[85%] border border-border text-card-foreground shadow-sm',
            isUser
              ? 'bg-primary text-primary-foreground rounded-tr-sm ml-auto'
              : 'bg-card rounded-tl-sm'
          )}
        >
          {message.isVoice && (
            <div className={cn(
              'flex items-center gap-1.5 text-xs mb-2 pb-2 border-b',
              isUser ? 'border-primary-foreground/20 text-primary-foreground/70' : 'border-border text-muted-foreground'
            )}>
              <Mic className="h-3 w-3" />
              <span>Voice message</span>
              {!isUser && message.audioUrl && (
                <div className="ml-auto flex gap-1">
                  {!isPlayingAudio ? (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={playAudio}
                      className="h-6 px-2 text-xs"
                    >
                      <Volume2 className="h-3 w-3 mr-1" />
                      Play
                    </Button>
                  ) : (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={pauseAudio}
                      className="h-6 px-2 text-xs"
                    >
                      <Pause className="h-3 w-3 mr-1" />
                      Pause
                    </Button>
                  )}
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={restartAudio}
                    disabled={!audioRef.current}
                    className="h-6 px-2 text-xs"
                  >
                    <RotateCcw className="h-3 w-3 mr-1" />
                    Restart
                  </Button>
                </div>
              )}
            </div>
          )}
          <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
        </div>

        {/* Metadata for assistant messages */}
        {!isUser && (
          <div className="flex flex-wrap items-center gap-2 px-1">
            {message.cached && (
              <span className="flex items-center gap-1 text-xs text-muted-foreground">
                <Zap className="h-3 w-3 text-warning" />
                Cached
              </span>
            )}
            
            {isLowConfidence && (
              <span className="flex items-center gap-1 text-xs text-warning">
                <AlertTriangle className="h-3 w-3" />
                Low confidence
              </span>
            )}

            {message.confidence !== undefined && !isLowConfidence && (
              <span className="text-xs text-muted-foreground">
                {Math.round(message.confidence * 100)}% confidence
              </span>
            )}
          </div>
        )}

        {/* Sources */}
        {message.sources && message.sources.length > 0 && (
          <div className="flex flex-wrap gap-2 px-1">
            <span className="text-xs font-medium text-muted-foreground">Sources:</span>
            {message.sources.map((source, index) => (
              <a
                key={index}
                href={source}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 rounded-full bg-secondary px-2.5 py-0.5 text-xs text-secondary-foreground hover:bg-secondary/80 transition-colors"
              >
                <ExternalLink className="h-3 w-3" />
                {new URL(source).hostname.replace('www.', '')}
              </a>
            ))}
          </div>
        )}

        {/* Timestamp */}
        <span className="px-1 text-xs text-muted-foreground">
          {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </span>
      </div>
    </div>
  );
}
