"use client";

import * as React from "react";
import { ArrowRight, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export function EarlyAccessForm() {
  const [email, setEmail] = React.useState("");
  const [state, setState] = React.useState<"idle" | "error" | "done">("idle");

  function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    const valid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    if (!valid) {
      setState("error");
      return;
    }
    setState("done");
  }

  if (state === "done") {
    return (
      <div className="flex items-center gap-3 rounded-lg border border-ok/40 bg-bg-2/60 px-5 py-4 text-sm text-fg">
        <span className="flex size-6 items-center justify-center rounded-full bg-ok/15 text-ok">
          <Check className="size-3.5" strokeWidth={2.5} />
        </span>
        You are on the list. We will reach out about connecting your first arm.
      </div>
    );
  }

  return (
    <form onSubmit={onSubmit} noValidate className="w-full max-w-md">
      <div className="flex flex-col gap-3 sm:flex-row">
        <div className="flex-1">
          <label htmlFor="email" className="sr-only">
            Work email
          </label>
          <input
            id="email"
            type="email"
            inputMode="email"
            placeholder="you@company.com"
            value={email}
            onChange={(e) => {
              setEmail(e.target.value);
              if (state === "error") setState("idle");
            }}
            className={cn(
              "h-12 w-full rounded-md border bg-bg-2/60 px-4 text-sm text-fg placeholder:text-faint transition-colors duration-150 focus:outline-none focus-visible:border-accent",
              state === "error" ? "border-fail" : "border-line-strong",
            )}
          />
        </div>
        <Button type="submit" size="lg">
          Get early access
          <ArrowRight className="size-4 transition-transform duration-200 ease-[var(--ease-out-quart)] group-hover:translate-x-0.5" />
        </Button>
      </div>
      <p
        className={cn(
          "mt-2.5 font-mono text-xs",
          state === "error" ? "text-fail" : "text-faint",
        )}
      >
        {state === "error"
          ? "Enter a valid email address."
          : "No spam. Just an invite when your hardware can connect."}
      </p>
    </form>
  );
}
