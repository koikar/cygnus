import { ArrowRight } from "lucide-react";
import { Section, Eyebrow } from "@/components/ui/section";
import { Reveal } from "@/components/ui/reveal";

const OLD = [
  "A human demonstrates every task by hand",
  "Motions are hardcoded into fixed trajectories",
  "A changed object position breaks the workflow",
  "New tasks mean more demos and more engineering",
];

const NEW = [
  "A human defines the goal and the safety limits",
  "The agent explores the robot's real action space",
  "Failures are diagnosed, corrected, and retried",
  "What works is saved as a reusable reflex",
];

export function Shift() {
  return (
    <Section className="py-24 sm:py-28">
      <div className="mx-auto max-w-3xl text-center">
        <Reveal>
          <Eyebrow className="justify-center">The shift</Eyebrow>
        </Reveal>
        <Reveal delay={0.06}>
          <h2 className="mt-5 text-3xl font-semibold leading-tight tracking-[-0.02em] text-fg sm:text-[2.6rem]">
            From demonstration-first to exploration-first.
          </h2>
        </Reveal>
        <Reveal delay={0.12}>
          <p className="mt-5 text-base leading-relaxed text-muted">
            A human still owns the objective and the boundaries. The agent does
            the trial, the correction, and the workflow discovery.
          </p>
        </Reveal>
      </div>

      <Reveal delay={0.1}>
        <div className="mt-14 grid grid-cols-1 gap-px overflow-hidden rounded-xl border border-line bg-line md:grid-cols-[1fr_auto_1fr]">
          {/* old */}
          <div className="bg-bg-2/50 p-7 sm:p-9">
            <p className="font-mono text-xs uppercase tracking-[0.18em] text-faint">
              Demonstration-first / today
            </p>
            <ul className="mt-6 space-y-4">
              {OLD.map((item) => (
                <li
                  key={item}
                  className="flex items-start gap-3 text-sm leading-relaxed text-muted"
                >
                  <span className="mt-2 size-1 shrink-0 rounded-full bg-faint" />
                  {item}
                </li>
              ))}
            </ul>
          </div>

          {/* divider arrow */}
          <div className="flex items-center justify-center bg-bg-2/50 px-4 py-2 md:px-6">
            <span className="flex size-10 items-center justify-center rounded-full border border-accent/40 bg-accent-soft text-accent">
              <ArrowRight className="size-4" />
            </span>
          </div>

          {/* new */}
          <div className="bg-bg-3/60 p-7 sm:p-9">
            <p className="font-mono text-xs uppercase tracking-[0.18em] text-accent">
              Exploration-first / ReflexOS
            </p>
            <ul className="mt-6 space-y-4">
              {NEW.map((item) => (
                <li
                  key={item}
                  className="flex items-start gap-3 text-sm leading-relaxed text-fg"
                >
                  <span className="mt-1.5 size-1.5 shrink-0 rounded-full bg-accent" />
                  {item}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </Reveal>
    </Section>
  );
}
