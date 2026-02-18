import { type ComponentPropsWithRef, type CSSProperties, forwardRef } from "react";
import { cn } from "@/lib/utils/cn";

export const Center = forwardRef<HTMLDivElement, ComponentPropsWithRef<"div">>(
  ({ className, style, ...props }, ref) => {
    const merged: CSSProperties = {
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      ...style,
    };

    return <div ref={ref} className={cn(className)} style={merged} {...props} />;
  },
);

Center.displayName = "Center";
