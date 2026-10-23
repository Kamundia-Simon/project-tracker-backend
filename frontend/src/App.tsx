import { Suspense, lazy } from "react";
import { Show, UserButton } from "@clerk/react";
import { Navigate, Route, Routes } from "react-router-dom";
import { BrandLoader, PageLoader } from "@/components/BrandLoader";
import { DevAuthToken } from "@/components/DevAuthToken";
import { Landing } from "@/pages/Landing";

// Lazily loaded so moving between routes actually shows the brand loader rather
// than swapping instantly from an already-bundled module.
const AuthPage = lazy(() =>
  import("@/pages/AuthPage").then((m) => ({ default: m.AuthPage })),
);

/** Signed-out visitors are sent to sign-in; Clerk returns them to /dashboard after. */
function RequireAuth({ children }: { children: React.ReactNode }) {
  return (
    <>
      <Show when="signed-in">{children}</Show>
      <Show when="signed-out">
        <Navigate to="/sign-in" replace />
      </Show>
    </>
  );
}

/** Placeholder until the real dashboard lands in Pass B. */
function DashboardPlaceholder() {
  return (
    <div className="min-h-svh bg-canvas">
      <header className="flex items-center justify-between border-b border-line bg-surface px-6 py-3">
        <span className="text-sm font-medium text-ink">Project Tracker</span>
        <div className="flex items-center gap-2">
          <DevAuthToken />
          <UserButton />
        </div>
      </header>
      <main className="mx-auto max-w-[620px] px-6 py-20 text-center">
        <h1 className="text-xl font-semibold text-ink">Dashboard coming next</h1>
        <p className="mt-2 text-[13px] text-ink-muted">
          The backend is being built through to launch; these pages land after it.
        </p>
        <BrandLoader size={30} label="Dashboard in progress" className="mt-8" />
      </main>
    </div>
  );
}

function App() {
  return (
    <Suspense fallback={<PageLoader />}>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/sign-in/*" element={<AuthPage mode="sign-in" />} />
        <Route path="/sign-up/*" element={<AuthPage mode="sign-up" />} />
        <Route
          path="/dashboard"
          element={
            <RequireAuth>
              <DashboardPlaceholder />
            </RequireAuth>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Suspense>
  );
}

export default App;
