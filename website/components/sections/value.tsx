import { ArrowDownRight } from "lucide-react";
import { Section, Eyebrow } from "@/components/ui/section";
import { Reveal, Stagger, StaggerItem } from "@/components/ui/reveal";

const REDUCES = [
  "Human teleoperation hours",
  "Engineering setup time",
  "Task-specific programming",
  "Retraining cycles",
  "Failed deployments",
  "Downtime caused by edge cases",
  "The cost of adapting robots to new sites",
];

export function Value() {
  return (
    <Section className="py-24 sm:py-32">
      <div className="grid grid-cols-1 gap-12 lg:grid-cols-[0.9fr_1.1fr] lg:gap-16">
        <div>
          <Reveal>
            <Eyebrow>Business value</Eyebrow>
          </Reveal>
          <Reveal delay={0.06}>
            <h2 className="mt-5 text-3xl font-semibold leading-tight tracking-[-0.02em] text-fg sm:text-[2.6rem]">
              Cut the cost of putting robots to work.
            </h2>
          </Reveal>
          <Reveal delay={0.12}>
            <p className="mt-6 max-w-[46ch] text-base leading-relaxed text-muted">
              By moving trial, correction, and discovery onto the agent, ReflexOS
              targets the expensive parts of every deployment. These are the
              outcomes the system is built to deliver as it matures.
            </p>
          </Reveal>
        </div>

        <Stagger className="divide-y divide-line border-t border-line">
          {REDUCES.map((item) => (
            <StaggerItem key={item}>
              <div className="group flex items-center gap-4 py-4">
                <ArrowDownRight
                  className="size-4 text-accent transition-transform duration-200 group-hover:translate-x-0.5 group-hover:translate-y-0.5"
                  strokeWidth={1.8}
                />
                <span className="text-base tracking-tight text-fg">{item}</span>
              </div>
            </StaggerItem>
          ))}
        </Stagger>
      </div>

      <Reveal delay={0.1}>
        <figure className="mt-20 border-t border-line pt-12">
          <blockquote className="max-w-4xl text-2xl font-medium leading-snug tracking-[-0.01em] text-fg sm:text-[2rem]">
            The long-term vision is a new training layer for robot workers, where
            robots are not reprogrammed for every workflow but{" "}
            <span className="text-accent">
              learn through AI-guided operation, memory, and reflex formation.
            </span>
          </blockquote>
        </figure>
      </Reveal>
    </Section>
  );
}
