import { cn } from "@/lib/utils";

export function Section({
  id,
  children,
  className,
}: {
  id?: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <section id={id} className={cn("relative scroll-mt-20", className)}>
      <div className="mx-auto w-full max-w-[1200px] px-5 sm:px-8">{children}</div>
    </section>
  );
}

export function Eyebrow({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "flex items-center gap-3 font-mono text-[0.7rem] uppercase tracking-[0.22em] text-accent",
        className,
      )}
    >
      <span className="h-px w-6 bg-accent/50" />
      {children}
    </div>
  );
}
