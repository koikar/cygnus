"use client";

import * as React from "react";
import { motion, AnimatePresence, useReducedMotion } from "motion/react";
import { cn } from "@/lib/utils";

type Kind = "call" | "resp" | "fail" | "ok" | "note" | "save";

type Line = { id: number; kind: Kind; tool?: string; text: string };

const SCRIPT: Omit<Line, "id">[] = [
  { kind: "note", text: "goal: move package from table to left bin" },
  { kind: "call", tool: "get_state", text: "get_state()" },
  { kind: "resp", text: "6 joints nominal / gripper open / within limits" },
  { kind: "call", tool: "camera", text: "camera.capture()" },
  { kind: "resp", text: "package detected at x0.42 y-0.11 z0.06" },
  { kind: "call", tool: "move_joint", text: "move_to(approach_pose)" },
  { kind: "call", tool: "grip", text: "grip.close()" },
  { kind: "call", tool: "verify", text: "verify_pick()" },
  { kind: "fail", text: "grip empty -- grasp missed by 12mm" },
  { kind: "note", text: "reason: approach angle too steep, retry shallower" },
  { kind: "call", tool: "move_joint", text: "move_to(approach_pose, pitch -14deg)" },
  { kind: "call", tool: "grip", text: "grip.close()" },
  { kind: "call", tool: "verify", text: "verify_pick()" },
  { kind: "ok", text: "holding package / contact force 4.1N" },
  { kind: "call", tool: "move_joint", text: "move_to(bin_left)" },
  { kind: "call", tool: "grip", text: "grip.open()" },
  { kind: "ok", text: "package placed in left bin" },
  { kind: "save", text: "reflex saved: sort_to_left_bin (4 steps, 1 recovery)" },
];

const DELAYS: Partial<Record<Kind, number>> = {
  note: 950,
  call: 620,
  resp: 540,
  fail: 1050,
  ok: 760,
  save: 1400,
};

const KIND_STYLES: Record<Kind, string> = {
  call: "text-fg",
  resp: "text-faint",
  fail: "text-fail",
  ok: "text-ok",
  note: "text-muted italic",
  save: "text-accent",
};

function Prefix({ kind }: { kind: Kind }) {
  const map: Record<Kind, string> = {
    call: "->",
    resp: "  ",
    fail: " x",
    ok: " *",
    note: " #",
    save: " +",
  };
  return (
    <span
      className={cn(
        "select-none pr-3 font-mono text-xs",
        kind === "fail" && "text-fail",
        kind === "ok" && "text-ok",
        kind === "call" && "text-accent",
        kind === "save" && "text-accent",
        (kind === "note" || kind === "resp") && "text-faint",
      )}
    >
      {map[kind]}
    </span>
  );
}

export function ToolConsole({ className }: { className?: string }) {
  const reduce = useReducedMotion();
  const [count, setCount] = React.useState(reduce ? SCRIPT.length : 0);
  const [cycle, setCycle] = React.useState(0);

  React.useEffect(() => {
    if (reduce) return;
    let timer: ReturnType<typeof setTimeout>;

    function step(i: number) {
      if (i > SCRIPT.length) {
        timer = setTimeout(() => {
          setCycle((c) => c + 1);
          setCount(0);
          step(0);
        }, 2600);
        return;
      }
      setCount(i);
      const last = SCRIPT[Math.min(i, SCRIPT.length - 1)];
      const delay = DELAYS[last.kind] ?? 700;
      timer = setTimeout(() => step(i + 1), delay);
    }

    step(0);
    return () => clearTimeout(timer);
  }, [reduce]);

  const lines: Line[] = SCRIPT.slice(0, count).map((l, i) => ({
    ...l,
    id: cycle * 1000 + i,
  }));

  return (
    <div
      className={cn(
        "relative overflow-hidden rounded-xl border border-line-strong bg-bg-2/80 shadow-[0_30px_80px_-40px_oklch(0_0_0/0.9)] backdrop-blur-[1px]",
        className,
      )}
    >
      {/* title bar */}
      <div className="flex items-center justify-between border-b border-line px-4 py-3">
        <div className="flex items-center gap-2.5">
          <span className="relative flex h-2 w-2">
            <span className="fx-pulse absolute inline-flex h-full w-full rounded-full bg-ok" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-ok" />
          </span>
          <span className="font-mono text-xs tracking-tight text-muted">
            agent <span className="text-faint">/</span> reflexos-mcp
          </span>
        </div>
        <span className="font-mono text-[0.65rem] uppercase tracking-[0.2em] text-faint">
          live session
        </span>
      </div>

      {/* stream */}
      <div className="flex h-[340px] flex-col justify-end gap-1.5 overflow-hidden px-4 py-4 sm:h-[380px]">
        <AnimatePresence initial={false}>
          {lines.map((line) => (
            <motion.div
              key={line.id}
              layout
              initial={{ opacity: 0, transform: "translateY(8px)" }}
              animate={{ opacity: 1, transform: "translateY(0px)" }}
              transition={{ duration: 0.32, ease: [0.16, 1, 0.3, 1] }}
              className="flex items-start font-mono text-[0.82rem] leading-relaxed"
            >
              <Prefix kind={line.kind} />
              <span className={KIND_STYLES[line.kind]}>
                {line.tool && line.kind === "call" ? (
                  <>
                    <span className="text-accent">{line.tool}</span>
                    <span className="text-faint">
                      {line.text.slice(line.tool.length)}
                    </span>
                  </>
                ) : (
                  line.text
                )}
              </span>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      {/* footer hint */}
      <div className="flex items-center justify-between border-t border-line px-4 py-2.5">
        <span className="font-mono text-[0.65rem] text-faint">
          tools: get_state / camera / move_joint / grip / verify
        </span>
        <span className="font-mono text-[0.65rem] text-faint">explore -&gt; verify -&gt; save</span>
      </div>
    </div>
  );
}
