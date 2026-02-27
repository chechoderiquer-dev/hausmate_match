import type { ButtonHTMLAttributes } from "react";
import { cn } from "../../lib/utils";

type ButtonVariant = "primary" | "secondary" | "ghost";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
}

const variantClasses: Record<ButtonVariant, string> = {
  primary:
    "bg-[var(--color-action-primary)] text-[var(--color-text-inverse)] shadow-[var(--shadow-panel)] hover:-translate-y-0.5 hover:bg-[var(--color-action-primary-hover)]",
  secondary:
    "bg-[rgba(217,241,243,0.96)] text-[var(--color-accent-primary)] shadow-[var(--shadow-panel)] hover:-translate-y-0.5 hover:bg-[rgba(201,234,238,0.98)]",
  ghost:
    "bg-[var(--color-action-ghost)] text-[var(--color-text-secondary)] ring-1 ring-transparent hover:bg-[var(--color-surface-primary)]",
};

export function Button({
  className,
  type = "button",
  variant = "primary",
  ...props
}: ButtonProps) {
  return (
    <button
      className={cn(
        "inline-flex min-h-11 items-center justify-center rounded-[var(--radius-control)] px-5 py-3 text-[length:var(--text-body)] font-semibold tracking-[0.02em] transition disabled:cursor-not-allowed disabled:opacity-60",
        variantClasses[variant],
        className,
      )}
      type={type}
      {...props}
    />
  );
}
