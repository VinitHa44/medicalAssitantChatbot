import { AlertTriangle } from 'lucide-react';

export function DisclaimerBanner() {
  return (
    <div className="bg-warning/10 border-b border-warning/20 px-4 py-2">
      <div className="container mx-auto flex items-center justify-center gap-2 text-sm">
        <AlertTriangle className="h-4 w-4 text-warning flex-shrink-0" />
        <p className="text-foreground/80">
          <span className="font-medium">Disclaimer:</span> This is not a diagnostic tool. 
          Always consult a healthcare professional for medical advice.
        </p>
      </div>
    </div>
  );
}
