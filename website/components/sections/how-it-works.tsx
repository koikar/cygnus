import {
  Plug,
  Target,
  Play,
  Eye,
  Lightbulb,
  Bookmark,
  Zap,
  TrendingDown,
  RefreshCw,
} from "lucide-react";
import { Section, Eyebrow } from "@/components/ui/section";
import { Reveal, Stagger, StaggerItem } from "@/components/ui/reveal";

const STEPS = [
  {
    icon: Plug,
    title: "Expose the robot as tools",
    desc: "Joints, camera, gripper, movement, state, and safety limits all become MCP tools the agent can call.",
  },
  {
    icon: Target,
    title: "Give the agent a goal",
    desc: "A plain objective: pick, place, sort, inspect, or recover. No trajectory, no script.",
  },
  {
    icon: Play,
    title: "Let the agent operate",
    desc: "The agent inspects state, tests possible actions, and drives the arm in a real or simulated scene.",
  },
  {
    icon: Eye,
    title: "Observe the result",
    desc: "Camera and sensor feedback confirm whether the action actually succeeded or failed.",
  },
  {
    icon: Lightbulb,
    title: "Reason and correct",
    desc: "On failure the agent explains why, adjusts the grasp or approach, and tries a better strategy.",
  },
  {
    icon: Bookmark,
    title: "Record successful behavior",
    desc: "The movement, rationale, sensor state, and outcome are saved as robot memory.",
  },
  {
    icon: Zap,
    title: "Convert memory into reflexes",
    desc: "Repeated successful workflows stop needing reasoning and replay as fast, reliable skills.",
  },
  {
    icon: TrendingDown,
    title: "Reduce training time",
    desc: "Each future workflow needs fewer human demonstrations and less engineering intervention.",
  },
];

export function HowItWorks() {
  return (
    <Section id="how" className="py-24 sm:py-32">
      <div className="max-w-2xl">
        <Reveal>
          <Eyebrow>The AI-supervised training loop</Eyebrow>
        </Reveal>
        <Reveal delay={0.06}>
          <h2 className="mt-5 text-3xl font-semibold leading-tight tracking-[-0.02em] text-fg sm:text-[2.6rem]">
            Operate, observe, correct, remember.
          </h2>
        </Reveal>
        <Reveal delay={0.12}>
          <p className="mt-5 text-base leading-relaxed text-muted">
            The loop runs with the agent in control of the trial and error. It
            keeps tightening until a workflow is reliable enough to become a
            reflex.
          </p>
        </Reveal>
      </div>

      <Stagger className="mt-14 grid grid-cols-1 gap-x-12 gap-y-0 sm:grid-cols-2">
        {STEPS.map((s, i) => (
          <StaggerItem key={s.title}>
            <div className="group relative flex gap-5 border-t border-line py-7">
              <div className="flex flex-col items-center">
                <span className="flex size-10 shrink-0 items-center justify-center rounded-lg border border-line bg-bg-2 text-accent transition-colors group-hover:border-accent/50">
                  <s.icon className="size-[18px]" strokeWidth={1.6} />
                </span>
              </div>
              <div className="pt-0.5">
                <span className="font-mono text-xs text-faint">
                  {String(i + 1).padStart(2, "0")}
                </span>
                <h3 className="mt-1 text-lg font-medium tracking-tight text-fg">
                  {s.title}
                </h3>
                <p className="mt-1.5 max-w-[42ch] text-sm leading-relaxed text-muted">
                  {s.desc}
                </p>
              </div>
            </div>
          </StaggerItem>
        ))}
      </Stagger>

      <Reveal>
        <div className="mt-10 flex items-center gap-3 font-mono text-xs text-faint">
          <RefreshCw className="size-3.5 text-accent" />
          The loop repeats: every recovery makes the next attempt cheaper.
        </div>
      </Reveal>
    </Section>
  );
}
