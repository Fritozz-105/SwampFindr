import { type ComponentPropsWithRef, type CSSProperties, forwardRef } from "react";
import { cn } from "@/lib/utils/cn";

type ColumnProps = ComponentPropsWithRef<"div"> & {
  gap?: number;
};

export const Column = forwardRef<HTMLDivElement, ColumnProps>(
  ({ className, gap, style, ...props }, ref) => {
    const merged: CSSProperties = {
      display: "flex",
      flexDirection: "column",
      ...style,
    };
    if (gap !== undefined) merged.gap = gap;

    return <div ref={ref} className={cn(className)} style={merged} {...props} />;
  },
);

Column.displayName = "Column";
