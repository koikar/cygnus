import { cn } from "@/lib/utils";

export function Logo({ className }: { className?: string }) {
  return (
    <span className={cn("flex items-center gap-2.5", className)}>
      <svg
        width="22"
        height="22"
        viewBox="0 0 24 24"
        fill="none"
        aria-hidden
        className="text-accent"
      >
        <rect
          x="1.5"
          y="1.5"
          width="21"
          height="21"
          rx="6"
          stroke="currentColor"
          strokeWidth="1.5"
          opacity="0.35"
        />
        <path
          d="M6 16.5V10.5L12 7L18 10.5"
          stroke="currentColor"
          strokeWidth="1.6"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <circle cx="12" cy="7" r="1.9" fill="currentColor" />
        <circle cx="6" cy="16.5" r="1.4" fill="currentColor" opacity="0.8" />
        <circle cx="18" cy="10.5" r="1.4" fill="currentColor" opacity="0.8" />
      </svg>
      <span className="text-[0.95rem] font-semibold tracking-tight text-fg">
        Reflex<span className="text-accent">OS</span>
      </span>
    </span>
  );
}
