import Image from "next/image";
import { Section, Eyebrow } from "@/components/ui/section";
import { Reveal, Stagger, StaggerItem } from "@/components/ui/reveal";

const METHODS = [
  {
    n: "01",
    title: "Human teleoperation",
    desc: "An operator drives the arm by hand for hours so the system has something to imitate.",
    image: "/images/teleoperation.jpg",
    imageAlt: "Warehouse engineer manually operating a robot arm with a teach pendant",
    imagePos: "center 40%",
  },
  {
    n: "02",
    title: "Leader-follower demonstrations",
    desc: "Every motion is shown on a second arm, then replayed and hand-tuned until it holds.",
    image: "/images/shift-old.jpg",
    imageAlt: "Engineer wearing a motion-capture exoskeleton to demonstrate robot movements",
    imagePos: "center 20%",
  },
  {
    n: "03",
    title: "Simulation datasets",
    desc: "Engineers build and label synthetic scenes that still break the moment reality differs.",
    image: "/images/sim-to-real.jpg",
    imageAlt: "Massive array of simulated robots with sim-to-real transfer visualization",
    imagePos: "center 30%",
  },
  {
    n: "04",
    title: "Endless correction loops",
    desc: "Policies are retuned, more data is collected, the robot is retrained, and the cycle repeats.",
    image: "/images/problem.jpg",
    imageAlt: "Robotics engineer frustrated after thousands of failed training episodes",
    imagePos: "center 25%",
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

      {/* 4-image evidence grid — one photo per bottleneck method */}
      <Reveal delay={0.28}>
        <div className="mt-14 grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-4">
          {METHODS.map((m) => (
            <div
              key={m.n}
              className="group overflow-hidden rounded-xl border border-line bg-bg-3 p-1 transition-colors duration-300 ease-(--ease-out-quart) hover:border-line-strong"
            >
              <div className="relative aspect-4/3 overflow-hidden rounded-[calc(0.75rem-2px)]">
                <Image
                  src={m.image}
                  alt={m.imageAlt}
                  fill
                  className="object-cover transition-transform duration-700 ease-(--ease-out-expo) group-hover:scale-[1.04]"
                  style={{ objectPosition: m.imagePos }}
                  sizes="(max-width: 640px) 50vw, (max-width: 1024px) 25vw, 280px"
                />
                {/* Very light atmospheric tint only */}
                <div className="absolute inset-0 bg-bg/15" />
                {/* Bottom gradient for label legibility */}
                <div className="absolute inset-x-0 bottom-0 h-20 bg-linear-to-t from-bg-3/95 to-transparent" />
                {/* Label */}
                <div className="absolute bottom-3 left-3.5 right-3">
                  <span className="font-mono text-[0.62rem] text-faint/90">{m.n}</span>
                  <p className="mt-0.5 text-[0.8rem] font-medium leading-snug tracking-tight text-fg">
                    {m.title}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </Reveal>
    </Section>
  );
}
