import { ClerkLoaded, ClerkLoading, SignIn, SignUp } from "@clerk/react";
import { Link } from "react-router-dom";
import { BrandLoader } from "@/components/BrandLoader";

/**
 * Clerk's own sign-in / sign-up, framed by the landing page's shell.
 * Registration stays whatever Clerk is configured to allow — if the instance is
 * invitation-only, this page inherits that; it never opens registration itself.
 */
export function AuthPage({ mode }: { mode: "sign-in" | "sign-up" }) {
  return (
    <div className="flex min-h-svh flex-col items-center justify-center gap-7 bg-canvas p-5">
      <Link to="/" className="flex items-center gap-2.5 rounded-lg">
        <span className="grid grid-cols-2 gap-[3px]" aria-hidden="true">
          <i className="block size-[7px] rounded-full bg-accent" />
          <i className="block size-[7px] rounded-full bg-ink" />
          <i className="block size-[7px] rounded-full bg-ink" />
          <i className="block size-[7px] rounded-full bg-ink" />
        </span>
        <span className="text-[15px] font-semibold tracking-[-0.01em] text-ink">
          3Gem <span className="text-ink-muted">Project Hub</span>
        </span>
      </Link>

      <ClerkLoading>
        <div className="flex min-h-[420px] items-center justify-center">
          <BrandLoader
            size={40}
            label={mode === "sign-in" ? "Loading sign in" : "Loading sign up"}
          />
        </div>
      </ClerkLoading>

      <ClerkLoaded>
        {mode === "sign-in" ? (
          <SignIn
            routing="path"
            path="/sign-in"
            signUpUrl="/sign-up"
            forceRedirectUrl="/dashboard"
          />
        ) : (
          <SignUp
            routing="path"
            path="/sign-up"
            signInUrl="/sign-in"
            forceRedirectUrl="/dashboard"
          />
        )}
      </ClerkLoaded>

      <Link
        to="/"
        className="rounded-lg text-[12.5px] text-ink-faint transition-colors hover:text-ink"
      >
        Back to the hub
      </Link>
    </div>
  );
}
