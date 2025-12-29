import { Heart, Stethoscope, Activity, Pill } from 'lucide-react';
import drAshaAvatar from '@/assets/dr-asha-avatar.png';

const suggestions = [
  { icon: Heart, text: "What are symptoms of diabetes?" },
  { icon: Stethoscope, text: "How can I manage high blood pressure?" },
  { icon: Activity, text: "What causes frequent headaches?" },
  { icon: Pill, text: "Tell me about healthy sleep habits" },
];

interface WelcomeMessageProps {
  onSuggestionClick?: (text: string) => void;
}

export function WelcomeMessage({ onSuggestionClick }: WelcomeMessageProps) {
  return (
    <div className="flex flex-col items-center text-center py-8 animate-fade-in-up">
      <img
        src={drAshaAvatar}
        alt="Dr. Asha"
        className="h-24 w-24 rounded-full border-4 border-primary/20 object-cover mb-4 shadow-lg"
      />
      <h2 className="text-2xl font-semibold text-foreground mb-2">
        Hello! I'm Dr. Asha
      </h2>
      <p className="text-muted-foreground max-w-md mb-8">
        Your AI-powered medical assistant. I can help answer your health questions 
        and provide general medical information. How can I assist you today?
      </p>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full max-w-lg">
        {suggestions.map((suggestion, index) => (
          <button
            key={index}
            onClick={() => onSuggestionClick?.(suggestion.text)}
            className="flex items-center gap-3 rounded-xl border border-border bg-card p-4 text-left transition-all hover:border-primary/50 hover:bg-secondary hover:shadow-md group"
          >
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10 text-primary group-hover:bg-primary group-hover:text-primary-foreground transition-colors">
              <suggestion.icon className="h-5 w-5" />
            </div>
            <span className="text-sm text-foreground">{suggestion.text}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
