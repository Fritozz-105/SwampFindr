import { type ComponentPropsWithRef, forwardRef } from "react";
import { cn } from "@/lib/utils/cn";

export const Box = forwardRef<HTMLDivElement, ComponentPropsWithRef<"div">>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn(className)} {...props} />
  ),
);

Box.displayName = "Box";
