import { cn } from "@/lib/utils";

export function Badge({
  children,
  className,
  dot = false,
}: {
  children: React.ReactNode;
  className?: string;
  dot?: boolean;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-2 rounded-full border border-line bg-bg-2/60 px-3 py-1 font-mono text-[0.7rem] uppercase tracking-[0.18em] text-muted",
        className,
      )}
    >
      {dot && (
        <span className="relative flex h-1.5 w-1.5">
          <span className="fx-pulse absolute inline-flex h-full w-full rounded-full bg-accent" />
          <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-accent" />
        </span>
      )}
      {children}
    </span>
  );
}
