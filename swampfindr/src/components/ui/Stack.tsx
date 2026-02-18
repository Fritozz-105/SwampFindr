import { type ComponentPropsWithRef, type CSSProperties, forwardRef } from "react";
import { cn } from "@/lib/utils/cn";

type StackProps = ComponentPropsWithRef<"div"> & {
  gap?: number;
};

export const Stack = forwardRef<HTMLDivElement, StackProps>(
  ({ className, gap = 16, style, ...props }, ref) => {
    const merged: CSSProperties = {
      display: "flex",
      flexDirection: "column",
      gap,
      ...style,
    };

    return <div ref={ref} className={cn(className)} style={merged} {...props} />;
  },
);

Stack.displayName = "Stack";
