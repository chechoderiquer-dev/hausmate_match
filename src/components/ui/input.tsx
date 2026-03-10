import type { InputHTMLAttributes } from "react";
import { cn } from "../../lib/utils";

export function Input({
  className,
  ...props
}: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={cn(
        "flex h-12 w-full rounded-[var(--radius-control)] border border-[var(--color-border-secondary)] bg-[var(--color-surface-strong)] px-4 text-[length:var(--text-body)] text-[var(--color-text-primary)] outline-none transition placeholder:text-[var(--color-text-muted)] focus:border-[var(--color-border-strong)] focus:ring-4 focus:ring-[var(--color-accent-soft)]",
        className,
      )}
      {...props}
    />
  );
}
