/** Dev-only button that copies the current Clerk session token, for testing endpoints in FastAPI's /docs. */

import { useState } from "react";
import { useAuth } from "@clerk/react";
import { Button } from "@/components/ui/button";

export function DevAuthToken() {
  const { getToken } = useAuth();
  const [copied, setCopied] = useState(false);

  if (!import.meta.env.DEV) return null;

  async function handleCopy() {
    const token = await getToken();
    if (!token) return;
    await navigator.clipboard.writeText(token);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <Button variant="outline" size="sm" onClick={handleCopy}>
      {copied ? "Copied" : "Copy token"}
    </Button>
  );
}
