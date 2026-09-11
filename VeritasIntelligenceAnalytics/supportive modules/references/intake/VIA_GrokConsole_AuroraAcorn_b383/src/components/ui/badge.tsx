import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium tracking-wide uppercase",
  {
    variants: {
      tone: {
        idle: "bg-elevated text-muted",
        pending: "bg-elevated text-subtle",
        ok: "bg-ok-dim text-ok",
        warn: "bg-warn-dim text-warn",
        bad: "bg-bad-dim text-bad",
        run: "bg-elevated text-accent",
        mute: "bg-transparent text-subtle shadow-[var(--shadow-border)]",
      },
    },
    defaultVariants: { tone: "idle" },
  },
);

export function Badge({
  className,
  tone,
  ...props
}: React.ComponentProps<"span"> & VariantProps<typeof badgeVariants>) {
  return <span className={cn(badgeVariants({ tone }), className)} {...props} />;
}
