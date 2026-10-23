import { useAuth } from "@clerk/react";
import { Link } from "react-router-dom";
import { CheckCircle, Circle, Timer } from "@phosphor-icons/react";
import { BrandLockup } from "@/components/landing/BrandLockup";
import { ArcAccent, RingPattern } from "@/components/landing/ArcAccent";
import { FloatingCard } from "@/components/landing/FloatingCard";
import { HeroShapes } from "@/components/landing/HeroShapes";

function Bar({ value, tone = "accent" }: { value: number; tone?: "accent" | "ok" }) {
  return (
    <span className="block h-1.5 flex-1 overflow-hidden rounded-full bg-surface-3">
      <span
        className={`block h-full rounded-full ${tone === "ok" ? "bg-ok" : "bg-accent"}`}
        style={{ width: `${value}%` }}
      />
    </span>
  );
}

/**
 * A compact stage rail — the same read as the project detail pipeline in
 * docs/mockups: what is done, where the project is now, what is still ahead.
 * Shows position in a sequence, not a percentage of anything.
 */
function StageRail({ steps }: { steps: Array<{ label: string; state: "done" | "current" | "todo" }> }) {
  return (
    <ol className="mt-2.5 flex items-center">
      {steps.map((step, i) => (
        <li key={step.label} className="flex flex-1 items-center last:flex-none">
          <span
            title={step.label}
            className={
              step.state === "done"
                ? "block size-2 rounded-full bg-ok"
                : step.state === "current"
                  ? "block size-2.5 rounded-full bg-accent ring-4 ring-[oklch(var(--accent)/0.22)]"
                  : "block size-2 rounded-full border-2 border-line-strong bg-surface"
            }
          />
          {i < steps.length - 1 && (
            <span
              className={`mx-1 h-0.5 flex-1 rounded-full ${
                step.state === "done" ? "bg-ok/70" : "bg-line-strong"
              }`}
            />
          )}
        </li>
      ))}
    </ol>
  );
}

export function Landing() {
  const { isSignedIn } = useAuth();

  return (
    <div className="relative min-h-svh overflow-hidden bg-[linear-gradient(135deg,oklch(var(--surface))_0%,oklch(var(--surface-2))_52%,oklch(var(--accent)/0.07)_100%)]">
      {/* Warm glow behind the headline so the colour reaches the text side too. */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -left-[12%] top-[6%] h-[640px] w-[640px] rounded-full bg-[radial-gradient(circle,oklch(var(--accent)/0.13)_0%,transparent_68%)] blur-[6px]"
      />
      {/* Shapes drift diagonally and fade into the page where they meet the text. */}
      <div className="pointer-events-none absolute inset-y-0 right-0 hidden w-[52%] overflow-hidden lg:block">
        <HeroShapes className="mask-fade-left animate-drift h-[124%] w-[124%] -translate-x-[12%] -translate-y-[12%]" />
      </div>
      {/* Mobile keeps a quiet trace of the same curve rather than the full composition. */}
      <HeroShapes className="animate-drift pointer-events-none absolute -right-24 top-0 h-[340px] w-[320px] opacity-70 lg:hidden" />

      {/* Soft rings anchored off the left edge — only their right arcs reach the page. */}
      <RingPattern className="pointer-events-none absolute -left-[30%] top-1/2 hidden h-[760px] w-[760px] -translate-y-1/2 lg:block" />

      {/* The dot-and-arc motif. Every arc obeys the same rule: the head sits on
          screen and the tail runs off an edge, so each reads as part of a larger
          curve passing through the page. Lengths and angles vary. */}
      <ArcAccent
        tone="ink"
        length="long"
        flip
        className="pointer-events-none absolute -left-[11%] top-[23%] hidden h-[170px] w-[340px] lg:block"
      />
      <ArcAccent
        tone="accent"
        length="long"
        className="pointer-events-none absolute -top-[13%] left-[13%] hidden h-[180px] w-[360px] -rotate-[68deg] lg:block"
      />
      <ArcAccent
        tone="ink"
        length="medium"
        flip
        className="pointer-events-none absolute -bottom-[14%] left-[33%] hidden h-[170px] w-[340px] -rotate-[122deg] opacity-80 lg:block"
      />
      <ArcAccent
        tone="accent"
        length="medium"
        flip
        className="pointer-events-none absolute -left-[13%] top-[46%] hidden h-[150px] w-[300px] opacity-75 lg:block"
      />
      <ArcAccent
        tone="ink"
        length="short"
        className="pointer-events-none absolute -top-[6%] left-[44%] hidden h-[130px] w-[260px] -rotate-[58deg] opacity-45 lg:block"
      />

      {/* Page-level, bottom left: balances the illustration column across the whole canvas. */}
      <img
        src="/landing/pinned-tasks.jpg"
        alt=""
        aria-hidden="true"
        className="hidden lg:absolute lg:bottom-[3%] lg:left-[3%] lg:z-20 lg:block lg:aspect-[4/5] lg:h-[180px] lg:w-[144px] lg:-rotate-[18deg] lg:rounded-xl lg:object-cover lg:shadow-[0_26px_54px_-26px_oklch(var(--ink)/0.5)] lg:ring-1 lg:ring-line lg:transition-transform lg:duration-200 lg:ease-out lg:hover:-translate-y-1 lg:hover:-rotate-[12deg]"
      />

      <header className="relative z-20 mx-auto flex max-w-[1340px] items-center justify-between px-6 py-2.5 lg:px-12">
        <Link to="/" className="rounded-lg" aria-label="3Gem Project Hub, home">
          <BrandLockup />
        </Link>

        {/* The pattern runs behind the header, so the links sit on their own surface. */}
        <nav
          className="flex items-center gap-1 rounded-full border border-line/70 bg-surface/75 p-1 backdrop-blur-md"
          aria-label="Account"
        >
          <Link
            to="/sign-in"
            className="rounded-full px-3.5 py-1.5 text-[13px] font-medium text-ink-muted transition-colors hover:bg-surface-2 hover:text-ink"
          >
            Sign in
          </Link>
          <Link
            to="/sign-up"
            className="rounded-full bg-ink px-3.5 py-1.5 text-[13px] font-medium text-surface transition-opacity hover:opacity-90"
          >
            Sign up
          </Link>
        </nav>
      </header>

      <main className="relative z-10 mx-auto grid max-w-[1340px] items-center gap-12 px-6 pb-16 pt-6 lg:min-h-[calc(100svh-60px)] lg:grid-cols-[1.02fr_1fr] lg:gap-8 lg:px-12 lg:pb-20 lg:pt-4">
        {/* Left — the message */}
        <div className="max-w-[560px]">
          <h1 className="text-[38px] font-semibold leading-[1.06] tracking-[-0.035em] text-ink sm:text-[52px] lg:text-[60px]">
            Every project. Every task.
            <span className="mt-2 block font-normal text-accent-strong">
              Moving <span className="font-semibold text-ink">3Gem</span> forward.
            </span>
          </h1>

          <p className="mt-6 max-w-[460px] text-[14.5px] leading-relaxed text-ink-muted">
            One shared workspace to organise projects, track tasks, manage milestones, and keep the
            3Gem team aligned on delivery.
          </p>

          <div className="mt-9 flex flex-wrap items-center gap-x-6 gap-y-3">
            {/* Always rendered: the page's only action must not wait on Clerk to load.
                Until auth resolves, sign-in is the safe destination — it forwards on. */}
            <Link
              to={isSignedIn ? "/dashboard" : "/sign-in"}
              className="inline-flex h-12 items-center justify-center rounded-xl bg-accent px-7 text-[15px] font-semibold text-accent-ink transition-[filter,transform] hover:brightness-[0.97] active:translate-y-px"
            >
              {isSignedIn ? "Go to your dashboard" : "Log in to Project Hub"}
            </Link>
            <Link
              to="/sign-up"
              className="rounded-lg text-[13.5px] font-medium text-ink-muted underline-offset-4 transition-colors hover:text-ink hover:underline"
            >
              Sign up
            </Link>
          </div>

          <p className="mt-5 text-[12px] text-ink-faint">Collaborative workspace for the 3Gem team.</p>
        </div>

        {/* Right — the illustration */}
        <div className="relative mx-auto w-full max-w-[460px] space-y-4 lg:h-[560px] lg:max-w-none lg:space-y-0">
          <FloatingCard
            title="My tasks"
            icon={<CheckCircle size={15} weight="duotone" className="text-accent-strong" />}
            className="w-full lg:absolute lg:right-0 lg:top-0 lg:w-[16.5rem] lg:-rotate-[3deg]"
          >
            <ul className="space-y-3">
              {[
                ["Set quotas", 100, true],
                ["Verify routings", 55, false],
                ["Soft launch", 20, false],
              ].map(([label, value, done]) => (
                <li key={label as string} className="space-y-1.5">
                  <div className="flex items-start gap-2">
                    {done ? (
                      <CheckCircle size={14} weight="fill" className="mt-px shrink-0 text-ok" />
                    ) : (
                      <Circle size={14} className="mt-px shrink-0 text-line-strong" />
                    )}
                    <span className="text-[12.5px] leading-snug text-ink">{label}</span>
                  </div>
                  <div className="flex items-center gap-2 pl-5">
                    <Bar value={value as number} tone={done ? "ok" : "accent"} />
                    <span className="w-7 text-right font-mono text-[10.5px] tabular-nums text-ink-faint">
                      {value}%
                    </span>
                  </div>
                </li>
              ))}
            </ul>
          </FloatingCard>

          {/* Milestone chip — staged, not a completion ring. */}
          <FloatingCard className="hidden lg:absolute lg:-left-[9%] lg:top-[70%] lg:block lg:w-[14.5rem] lg:rotate-[5deg]">
            <span className="flex items-center gap-1.5 text-[11px] text-ink-faint">
              <Timer size={12} weight="duotone" />
              Upcoming milestone
            </span>
            <span className="mt-0.5 block text-[12.5px] font-semibold text-ink">Project launch</span>
            <StageRail
              steps={[
                { label: "Scripting", state: "done" },
                { label: "QA", state: "done" },
                { label: "Client review", state: "done" },
                { label: "Quotas", state: "current" },
                { label: "Live", state: "todo" },
              ]}
            />
            <span className="mt-2 block text-[10.5px] text-ink-faint">Quotas &middot; next: Live</span>
          </FloatingCard>

          <FloatingCard
            title="Workload"
            className="w-full lg:absolute lg:bottom-[4%] lg:right-[2%] lg:w-[17rem] lg:rotate-[2deg]"
          >
            {/* Bars are scaled against the busiest team, so four reads as full and two as half. */}
            <ul className="space-y-3">
              {([
                ["Scripting team", 4],
                ["QA team", 2],
                ["Data team", 4],
              ] as const).map(([label, count]) => (
                <li key={label} className="space-y-1.5">
                  <div className="flex items-baseline justify-between gap-2">
                    <span className="truncate text-[12.5px] text-ink">{label}</span>
                    <span className="font-mono text-[10.5px] tabular-nums text-ink-faint">
                      {count} projects
                    </span>
                  </div>
                  <Bar value={(count / 4) * 100} />
                </li>
              ))}
            </ul>
          </FloatingCard>

          {/* Supplied reference photos, used as tilted previews rather than a gallery.
              Both are decorative, so they carry empty alt text and sit behind the cards. */}
          <img
            src="/landing/checklist-note.jpg"
            alt=""
            aria-hidden="true"
            className="hidden lg:absolute lg:left-[4%] lg:top-[1%] lg:block lg:aspect-[2/3] lg:h-[236px] lg:w-[157px] lg:rotate-[12deg] lg:rounded-xl lg:object-cover lg:shadow-[0_24px_50px_-26px_oklch(var(--ink)/0.5)] lg:ring-1 lg:ring-line lg:transition-transform lg:duration-200 lg:ease-out lg:hover:rotate-[6deg]"
          />
        </div>
      </main>
    </div>
  );
}

export default Landing;
