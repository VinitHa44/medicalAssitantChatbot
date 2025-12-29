import drAshaAvatar from '@/assets/dr-asha-avatar.png';

export function TypingIndicator() {
  return (
    <div className="flex gap-3 animate-fade-in-up">
      <img
        src={drAshaAvatar}
        alt="Dr. Asha"
        className="h-10 w-10 rounded-full border border-border object-cover flex-shrink-0"
      />
      <div className="flex items-center gap-1 rounded-2xl rounded-tl-sm bg-card border border-border px-4 py-3 shadow-sm">
        <span className="text-sm text-muted-foreground mr-2">Dr. Asha is thinking</span>
        <span className="h-2 w-2 rounded-full bg-primary animate-typing-dots" style={{ animationDelay: '0ms' }} />
        <span className="h-2 w-2 rounded-full bg-primary animate-typing-dots" style={{ animationDelay: '200ms' }} />
        <span className="h-2 w-2 rounded-full bg-primary animate-typing-dots" style={{ animationDelay: '400ms' }} />
      </div>
    </div>
  );
}
