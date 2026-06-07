import { Check } from "lucide-react";
import { Section, Eyebrow } from "@/components/ui/section";
import { Reveal } from "@/components/ui/reveal";

const LEARNED = [
  "How to approach the object",
  "Which grasp angle actually works",
  "Which joint sequence stays safe",
  "How to verify the object was picked",
  "How to recover from a missed grasp",
  "How to place it in the correct bin",
];

export function UseCase() {
  return (
    <Section id="use-case" className="py-24 sm:py-32">
      <div className="grid grid-cols-1 items-center gap-12 lg:grid-cols-[1.05fr_0.95fr] lg:gap-16">
        <div>
          <Reveal>
            <Eyebrow>Use case / warehouse sorting</Eyebrow>
          </Reveal>
          <Reveal delay={0.06}>
            <h2 className="mt-5 text-3xl font-semibold leading-tight tracking-[-0.02em] text-fg sm:text-[2.6rem]">
              A sorting robot that trains itself on the line.
            </h2>
          </Reveal>
          <Reveal delay={0.12}>
            <p className="mt-6 max-w-[52ch] text-base leading-relaxed text-muted">
              Traditionally, engineers collect demonstrations, program fixed
              motions, test edge cases, and hand-correct failures. Move the
              package or miss the grip, and the workflow breaks.
            </p>
          </Reveal>
          <Reveal delay={0.18}>
            <p className="mt-4 max-w-[52ch] text-base leading-relaxed text-muted">
              With ReflexOS the arm connects as an MCP server. The agent sees the
              package, checks joint state, tests a grasp, verifies the pick, and
              places it. When it misses, it does not stop. It reasons about the
              failure, tries a new grasp, and saves the recovery.
            </p>
          </Reveal>
        </div>

        <Reveal delay={0.1} y={24}>
          <div className="overflow-hidden rounded-xl border border-line-strong bg-bg-2/70 shadow-[0_30px_80px_-50px_oklch(0_0_0/0.9)]">
            <div className="flex items-center justify-between border-b border-line px-5 py-3.5">
              <span className="font-mono text-xs text-muted">
                reflex <span className="text-accent">sort_to_left_bin</span>
              </span>
              <span className="flex items-center gap-1.5 font-mono text-[0.65rem] uppercase tracking-[0.18em] text-ok">
                <span className="size-1.5 rounded-full bg-ok" />
                learned
              </span>
            </div>
            <ul className="divide-y divide-line">
              {LEARNED.map((item) => (
                <li
                  key={item}
                  className="flex items-center gap-3 px-5 py-3.5 text-sm text-fg"
                >
                  <Check className="size-4 shrink-0 text-ok" strokeWidth={2} />
                  {item}
                </li>
              ))}
            </ul>
            <div className="border-t border-line px-5 py-3 font-mono text-[0.7rem] text-faint">
              built from real attempts: 4 steps, 1 recovery, 0 human demos
            </div>
          </div>
        </Reveal>
      </div>
    </Section>
  );
}
