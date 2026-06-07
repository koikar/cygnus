import { Logo } from "@/components/ui/logo";

const COLUMNS = [
  {
    title: "Product",
    links: [
      { href: "#problem", label: "Problem" },
      { href: "#how", label: "How it works" },
      { href: "#features", label: "Capabilities" },
      { href: "#use-case", label: "Use case" },
    ],
  },
  {
    title: "More",
    links: [
      { href: "#faq", label: "FAQ" },
      { href: "#access", label: "Early access" },
      { href: "#top", label: "Back to top" },
    ],
  },
];

export function Footer() {
  return (
    <footer className="mt-auto border-t border-line">
      <div className="mx-auto w-full max-w-[1200px] px-5 py-14 sm:px-8">
        <div className="grid grid-cols-2 gap-10 sm:grid-cols-4">
          <div className="col-span-2">
            <Logo />
            <p className="mt-4 max-w-xs text-sm leading-relaxed text-muted">
              An AI-native training layer for robot workers. Operate, learn, and
              form reflexes through MCP.
            </p>
          </div>

          {COLUMNS.map((col) => (
            <div key={col.title}>
              <p className="font-mono text-[0.7rem] uppercase tracking-[0.18em] text-faint">
                {col.title}
              </p>
              <ul className="mt-4 space-y-2.5">
                {col.links.map((l) => (
                  <li key={l.label}>
                    <a
                      href={l.href}
                      className="text-sm text-muted transition-colors hover:text-fg"
                    >
                      {l.label}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="mt-12 flex flex-col gap-3 border-t border-line pt-6 sm:flex-row sm:items-center sm:justify-between">
          <p className="font-mono text-xs text-faint">
            ReflexOS / 2026 / Built at the Euro-Tech Hackathon
          </p>
          <p className="font-mono text-xs text-faint">
            Human-defined goals. Agent-driven training.
          </p>
        </div>
      </div>
    </footer>
  );
}
