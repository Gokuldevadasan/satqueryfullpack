import type { ComponentPropsWithoutRef, ReactNode } from "react";

type LiquidGlassProps = ComponentPropsWithoutRef<"div"> & { children: ReactNode };

export function LiquidGlass({ children, className = "", ...props }: LiquidGlassProps) {
  return <div className={`liquid-glass ${className}`} {...props}>{children}</div>;
}
