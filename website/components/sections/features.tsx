import {
  Cpu,
  Compass,
  Zap,
  Repeat2,
  FlaskConical,
  ShieldHalf,
} from "lucide-react";
import { Section, Eyebrow } from "@/components/ui/section";
import { Bento, BentoTile } from "@/components/ui/bento";
import { Reveal, Stagger, StaggerItem } from "@/components/ui/reveal";

const TOOLS = [
  { sig: "get_state()", out: "joint angles, forces" },
  { sig: "camera.capture()", out: "scene frame" },
  { sig: "move_to(pose)", out: "constrained motion" },
  { sig: "grip.open / close()", out: "actuation" },
  { sig: "verify(goal)", out: "success | failure" },
  { sig: "home() / limits()", out: "safe pose, bounds" },
];

export function Features() {
  return (
    <Section id="features" className="py-24 sm:py-32">
      <div className="max-w-2xl">
        <Reveal>
          <Eyebrow>What the agent works with</Eyebrow>
        </Reveal>
        <Reveal delay={0.06}>
          <h2 className="mt-5 text-3xl font-semibold leading-tight tracking-[-0.02em] text-fg sm:text-[2.6rem]">
            One standard interface for the whole robot.
          </h2>
        </Reveal>
        <Reveal delay={0.12}>
          <p className="mt-5 text-base leading-relaxed text-muted">
            MCP turns the robot into something an agent can read and reason
            about, not a black box behind a custom SDK.
          </p>
        </Reveal>
      </div>

      <Stagger className="mt-14">
        <Bento>
          {/* Tall left tile: the tool inventory */}
          <StaggerItem className="lg:col-span-3 lg:row-span-2">
            <BentoTile
              icon={Cpu}
              title="The robot's body, as tools"
              desc="Camera, state, joints, gripper, movement, home position, and safety limits are exposed as callable MCP tools. Each action becomes part of an action space the agent understands."
              className="h-full"
            >
              <div className="divide-y divide-line rounded-lg border border-line bg-bg/40">
                {TOOLS.map((t) => (
                  <div
                    key={t.sig}
                    className="flex items-center justify-between gap-4 px-4 py-2.5 font-mono text-[0.78rem]"
                  >
                    <span className="text-accent">{t.sig}</span>
                    <span className="text-faint">{t.out}</span>
                  </div>
                ))}
              </div>
            </BentoTile>
          </StaggerItem>

          <StaggerItem className="lg:col-span-3">
            <BentoTile
              icon={Compass}
              title="Agent-driven exploration"
              desc="The agent inspects state, sees which movements are possible, tries positions, watches outcomes, and corrects, instead of waiting for a human to demonstrate."
              className="h-full"
            />
          </StaggerItem>

          <StaggerItem className="lg:col-span-3">
            <BentoTile
              icon={Zap}
              title="Memory becomes reflexes"
              desc="A successful trajectory, its rationale and sensor state are stored. Seen again, the workflow replays as a fast reflex instead of reasoning from scratch."
              className="h-full"
            />
          </StaggerItem>

          <StaggerItem className="lg:col-span-2">
            <BentoTile
              icon={Repeat2}
              title="Cross-robot skill transfer"
              desc="A skill is a workflow, not a fixed motion path. If a new arm exposes equivalent tools, the agent retests and saves a robot-specific reflex."
              className="h-full"
            />
          </StaggerItem>

          <StaggerItem className="lg:col-span-2">
            <BentoTile
              icon={FlaskConical}
              title="Synthetic-to-real correction"
              desc="The agent compares the simulated plan with the real outcome, finds where it broke, and records the physical correction as reusable memory."
              className="h-full"
            />
          </StaggerItem>

          <StaggerItem className="lg:col-span-2">
            <BentoTile
              icon={ShieldHalf}
              title="Human-owned boundaries"
              desc="People define the objective and the safety envelope. Joint and force limits stay enforced while the agent does the trial and error."
              className="h-full"
            />
          </StaggerItem>
        </Bento>
      </Stagger>
    </Section>
  );
}
