import type { ButtonHTMLAttributes } from "react";
import { cn } from "../../lib/utils";

type ButtonVariant = "primary" | "secondary" | "ghost";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
}

const variantClasses: Record<ButtonVariant, string> = {
  primary:
    "bg-[var(--color-action-primary)] text-[var(--color-text-inverse)] shadow-[var(--color-button-shadow)] hover:-translate-y-0.5 hover:bg-[var(--color-action-primary-hover)]",
  secondary:
    "bg-[var(--color-action-secondary)] text-[var(--color-accent-primary)] shadow-[var(--color-button-shadow)] hover:-translate-y-0.5 hover:bg-[var(--color-action-secondary-hover)]",
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
        "inline-flex min-h-11 appearance-none items-center justify-center rounded-[var(--radius-control)] border border-transparent px-5 py-3 text-[length:var(--text-body)] font-semibold tracking-[0.02em] transition disabled:cursor-not-allowed disabled:opacity-100",
        variantClasses[variant],
        className,
      )}
      type={type}
      {...props}
    />
  );
}
