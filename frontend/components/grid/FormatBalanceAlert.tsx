"use client";

interface FormatData {
  name: string;
  count: number;
  percentage: number;
}

interface FormatBalanceAlertProps {
  formats: FormatData[];
}

export function FormatBalanceAlert({ formats }: FormatBalanceAlertProps) {
  if (!formats || formats.length === 0) return null;

  const skewed = formats.find((f) => f.percentage > 70);
  if (!skewed) return null;

  return (
    <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 dark:border-amber-800 dark:bg-amber-900/20">
      <div className="flex items-start gap-2">
        <span className="text-amber-600 dark:text-amber-400 text-sm font-medium">⚠</span>
        <div>
          <p className="text-sm font-medium text-amber-800 dark:text-amber-300">
            Format imbalance detected
          </p>
          <p className="mt-1 text-xs text-amber-700 dark:text-amber-400">
            Your content is heavily skewed toward <strong>{skewed.name}</strong> ({skewed.percentage}%).
            Consider adding other formats for deeper engagement.
          </p>
        </div>
      </div>
    </div>
  );
}
