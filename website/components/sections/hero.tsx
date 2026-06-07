import { ArrowRight, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ToolConsole } from "@/components/ui/tool-console";
import { Reveal } from "@/components/ui/reveal";

export function Hero() {
  return (
    <section id="top" className="relative scroll-mt-20">
      <div className="mx-auto grid w-full max-w-[1200px] grid-cols-1 items-center gap-12 px-5 pb-20 pt-16 sm:px-8 lg:grid-cols-[1.04fr_0.96fr] lg:gap-14 lg:pb-28 lg:pt-24">
        {/* left: copy */}
        <div className="flex flex-col items-start">
          <Reveal>
            <Badge dot>Early access / Euro-Tech Hackathon</Badge>
          </Reveal>

          <Reveal delay={0.06}>
            <h1 className="mt-6 max-w-[15ch] text-[2.6rem] font-semibold leading-[1.02] tracking-[-0.03em] text-fg sm:text-6xl">
              Robots that learn the job themselves.
            </h1>
          </Reveal>

          <Reveal delay={0.12}>
            <p className="mt-6 max-w-[52ch] text-lg leading-relaxed text-muted">
              ReflexOS turns a robot arm into an MCP server. An AI agent operates
              it, watches what happens, recovers from its own mistakes, and saves
              what works as a reusable reflex, so a new task needs far less
              teleoperation and engineering.
            </p>
          </Reveal>

          <Reveal delay={0.18}>
            <div className="mt-9 flex flex-col gap-3 sm:flex-row sm:items-center">
              <Button href="#access" size="lg">
                Get early access
                <ArrowRight className="size-4 transition-transform duration-200 ease-[var(--ease-out-quart)] group-hover:translate-x-0.5" />
              </Button>
              <Button href="#how" size="lg" variant="secondary">
                See the training loop
              </Button>
            </div>
          </Reveal>

          <Reveal delay={0.24}>
            <div className="mt-10 flex flex-wrap items-center gap-x-6 gap-y-2 font-mono text-xs text-faint">
              <span className="flex items-center gap-2">
                <ShieldCheck className="size-3.5 text-accent" />
                Human-defined goals & safety limits
              </span>
              <span className="hidden h-3 w-px bg-line sm:block" />
              <span>Built for logistics, ports, warehouses & manufacturing</span>
            </div>
          </Reveal>
        </div>

        {/* right: live agent console */}
        <Reveal delay={0.1} y={24}>
          <div className="relative">
            <div
              aria-hidden
              className="absolute -inset-4 -z-10 rounded-2xl bg-[radial-gradient(60%_50%_at_70%_0%,var(--accent-soft),transparent_70%)]"
            />
            <ToolConsole />
          </div>
        </Reveal>
      </div>
    </section>
  );
}
