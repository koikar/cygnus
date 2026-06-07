import Image from "next/image";
import type { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

export function Bento({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-6",
        className,
      )}
    >
      {children}
    </div>
  );
}

export function BentoTile({
  icon: Icon,
  title,
  desc,
  children,
  className,
  bgImage,
}: {
  icon: LucideIcon;
  title: string;
  desc: string;
  children?: React.ReactNode;
  className?: string;
  bgImage?: string;
}) {
  return (
    <div
      className={cn(
        "group relative flex flex-col overflow-hidden rounded-xl border border-line bg-bg-2/50 p-7 transition-colors duration-300 ease-[var(--ease-out-quart)] hover:border-line-strong",
        className,
      )}
    >
      {/* Optional photo background */}
      {bgImage && (
        <div className="pointer-events-none absolute inset-0 z-0">
          <Image
            src={bgImage}
            alt=""
            fill
            className="object-cover opacity-[0.18] transition-opacity duration-500 ease-[var(--ease-out-quart)] group-hover:opacity-[0.28]"
            sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-bg-2/95 via-bg-2/70 to-bg-2/20" />
        </div>
      )}

      {/* Hover top-edge highlight */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-x-0 top-0 z-20 h-px bg-gradient-to-r from-transparent via-accent/40 to-transparent opacity-0 transition-opacity duration-300 group-hover:opacity-100"
      />

      {/* Content */}
      <div className={cn("relative flex flex-1 flex-col", bgImage && "z-10")}>
        <span className="flex size-10 items-center justify-center rounded-lg border border-line bg-bg-3 text-accent">
          <Icon className="size-[18px]" strokeWidth={1.6} />
        </span>
        <h3 className="mt-5 text-lg font-medium tracking-tight text-fg">
          {title}
        </h3>
        <p className="mt-2 max-w-[44ch] text-sm leading-relaxed text-muted">
          {desc}
        </p>
        {children && <div className="mt-6 flex-1">{children}</div>}
      </div>
    </div>
  );
}
