"use client";

import * as React from "react";
import { motion, AnimatePresence } from "motion/react";
import { Plus } from "lucide-react";
import { Section, Eyebrow } from "@/components/ui/section";
import { Reveal } from "@/components/ui/reveal";
import { cn } from "@/lib/utils";

const ITEMS = [
  {
    q: "Which robots does ReflexOS work with?",
    a: "Any arm that can expose its camera, state, joints, gripper, movement, home position, and safety limits as MCP tools. The interface is what matters, not the specific brand of hardware.",
  },
  {
    q: "What is MCP, and why build on it?",
    a: "MCP is a standard tool interface. It lets an AI agent read and call the robot's actions in a consistent way, so a skill can be expressed as an agent-readable workflow rather than a fragile, hardcoded motion path.",
  },
  {
    q: "Is it safe to let an agent operate hardware?",
    a: "A human defines the objective and the safety envelope. Joint and force limits stay enforced as constraints, and the agent does its trial and error strictly inside those boundaries.",
  },
  {
    q: "How does what the robot learns persist?",
    a: "Successful trajectories, the agent's rationale, sensor state, and outcome are saved as robot memory. After repeated success the workflow is promoted to a fast reflex, so it no longer reasons from scratch.",
  },
  {
    q: "Does this replace simulation?",
    a: "No. It bridges simulation and reality by comparing the simulated plan against the real outcome, locating where the plan broke, and recording the physical correction for future sim-to-real transfers.",
  },
  {
    q: "How would we get started?",
    a: "Connect a robot or simulator as an MCP server, set a goal and the safety limits, and let the agent run the loop. ReflexOS is in early access, built at the Euro-Tech Hackathon.",
  },
];

function Item({
  q,
  a,
  open,
  onToggle,
}: {
  q: string;
  a: string;
  open: boolean;
  onToggle: () => void;
}) {
  return (
    <div className="border-t border-line">
      <button
        onClick={onToggle}
        aria-expanded={open}
        className="flex w-full items-center justify-between gap-6 py-5 text-left"
      >
        <span className="text-base font-medium tracking-tight text-fg sm:text-lg">
          {q}
        </span>
        <Plus
          className={cn(
            "size-4 shrink-0 text-accent transition-transform duration-300 ease-[var(--ease-out-quart)]",
            open && "rotate-45",
          )}
        />
      </button>
      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
            className="overflow-hidden"
          >
            <p className="max-w-[64ch] pb-6 text-sm leading-relaxed text-muted sm:text-[0.95rem]">
              {a}
            </p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export function Faq() {
  const [open, setOpen] = React.useState<number | null>(0);

  return (
    <Section id="faq" className="py-24 sm:py-32">
      <div className="grid grid-cols-1 gap-12 lg:grid-cols-[0.65fr_1.35fr] lg:gap-16">
        <div>
          <Reveal>
            <Eyebrow>Questions</Eyebrow>
          </Reveal>
          <Reveal delay={0.06}>
            <h2 className="mt-5 text-3xl font-semibold leading-tight tracking-[-0.02em] text-fg sm:text-4xl">
              Answers before you connect an arm.
            </h2>
          </Reveal>
        </div>

        <Reveal delay={0.1}>
          <div className="border-b border-line">
            {ITEMS.map((item, i) => (
              <Item
                key={item.q}
                q={item.q}
                a={item.a}
                open={open === i}
                onToggle={() => setOpen(open === i ? null : i)}
              />
            ))}
          </div>
        </Reveal>
      </div>
    </Section>
  );
}
