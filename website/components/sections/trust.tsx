import { Boxes, Ship, Warehouse, Factory } from "lucide-react";
import { Reveal } from "@/components/ui/reveal";

const ENVIRONMENTS = [
  { icon: Boxes, label: "Logistics" },
  { icon: Ship, label: "Ports" },
  { icon: Warehouse, label: "Warehouses" },
  { icon: Factory, label: "Manufacturing" },
];

export function Trust() {
  return (
    <Reveal>
      <div className="border-y border-line">
        <div className="mx-auto flex w-full max-w-[1200px] flex-col gap-6 px-5 py-8 sm:flex-row sm:items-center sm:justify-between sm:px-8">
          <p className="max-w-xs font-mono text-xs uppercase tracking-[0.18em] text-faint">
            Built for the places where every workflow is a little different
          </p>
          <div className="grid grid-cols-2 gap-x-10 gap-y-4 sm:flex sm:items-center sm:gap-9">
            {ENVIRONMENTS.map(({ icon: Icon, label }) => (
              <div
                key={label}
                className="flex items-center gap-2.5 text-muted"
              >
                <Icon className="size-4 text-accent" strokeWidth={1.5} />
                <span className="text-sm tracking-tight">{label}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </Reveal>
  );
}
