import type { InputHTMLAttributes } from "react";
import { cn } from "../../lib/utils";

export function Checkbox({
  className,
  ...props
}: Omit<InputHTMLAttributes<HTMLInputElement>, "type">) {
  return (
    <input
      className={cn(
        "mt-1 h-5 w-5 rounded border-[var(--color-border-strong)] accent-[var(--color-action-primary)]",
        className,
      )}
      type="checkbox"
      {...props}
    />
  );
}
