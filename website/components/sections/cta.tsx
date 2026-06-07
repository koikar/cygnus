import { Section } from "@/components/ui/section";
import { Badge } from "@/components/ui/badge";
import { Reveal } from "@/components/ui/reveal";
import { EarlyAccessForm } from "@/components/ui/early-access-form";

export function Cta() {
  return (
    <Section id="access" className="py-24 sm:py-32">
      <div className="relative overflow-hidden rounded-2xl border border-line-strong bg-bg-2/60 px-6 py-16 sm:px-12 sm:py-20">
        <div
          aria-hidden
          className="pointer-events-none absolute inset-x-0 top-0 -z-0 h-64 bg-[radial-gradient(70%_100%_at_50%_0%,var(--accent-soft),transparent_70%)]"
        />
        <div className="relative mx-auto flex max-w-2xl flex-col items-center text-center">
          <Reveal>
            <Badge dot>Early access</Badge>
          </Reveal>
          <Reveal delay={0.06}>
            <h2 className="mt-6 text-3xl font-semibold leading-[1.05] tracking-[-0.02em] text-fg sm:text-5xl">
              Let the agent do the training.
            </h2>
          </Reveal>
          <Reveal delay={0.12}>
            <p className="mt-5 max-w-[48ch] text-base leading-relaxed text-muted sm:text-lg">
              Connect a robot as an MCP server, set a goal and safety limits, and
              watch it learn the workflow, recover from failures, and turn what
              works into reflexes.
            </p>
          </Reveal>
          <Reveal delay={0.18}>
            <div className="mt-9 flex justify-center">
              <EarlyAccessForm />
            </div>
          </Reveal>
        </div>
      </div>
    </Section>
  );
}
