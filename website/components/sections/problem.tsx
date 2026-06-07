import { Section, Eyebrow } from "@/components/ui/section";
import { Reveal, Stagger, StaggerItem } from "@/components/ui/reveal";

const METHODS = [
  {
    n: "01",
    title: "Human teleoperation",
    desc: "An operator drives the arm by hand for hours so the system has something to imitate.",
  },
  {
    n: "02",
    title: "Leader-follower demonstrations",
    desc: "Every motion is shown on a second arm, then replayed and hand-tuned until it holds.",
  },
  {
    n: "03",
    title: "Simulation datasets",
    desc: "Engineers build and label synthetic scenes that still break the moment reality differs.",
  },
  {
    n: "04",
    title: "Endless correction loops",
    desc: "Policies are retuned, more data is collected, the robot is retrained, and the cycle repeats.",
  },
];

export function Problem() {
  return (
    <Section id="problem" className="py-24 sm:py-32">
      <div className="grid grid-cols-1 gap-12 lg:grid-cols-[0.85fr_1.15fr] lg:gap-16">
        <div>
          <Reveal>
            <Eyebrow>The bottleneck</Eyebrow>
          </Reveal>
          <Reveal delay={0.06}>
            <h2 className="mt-5 text-3xl font-semibold leading-tight tracking-[-0.02em] text-fg sm:text-[2.6rem]">
              Teaching a robot a new task is still slow, costly, and human-bound.
            </h2>
          </Reveal>
          <Reveal delay={0.12}>
            <p className="mt-6 max-w-[46ch] text-base leading-relaxed text-muted">
              The real cost is rarely the hardware. It is the time and expertise
              needed to adapt the robot to each new environment, object, and
              workflow. Today that adaptation looks like one of these, usually
              all of them.
            </p>
          </Reveal>
        </div>

        <Stagger className="divide-y divide-line border-t border-line">
          {METHODS.map((m) => (
            <StaggerItem key={m.n}>
              <div className="group flex items-start gap-5 py-6">
                <span className="font-mono text-sm text-faint transition-colors group-hover:text-accent">
                  {m.n}
                </span>
                <div>
                  <h3 className="text-lg font-medium tracking-tight text-fg">
                    {m.title}
                  </h3>
                  <p className="mt-1.5 max-w-[54ch] text-sm leading-relaxed text-muted">
                    {m.desc}
                  </p>
                </div>
              </div>
            </StaggerItem>
          ))}
        </Stagger>
      </div>
    </Section>
  );
}
