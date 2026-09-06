"use client";

import { useState, useEffect, useCallback } from "react";
import { usePathname } from "next/navigation";
import { SplashScreen } from "@/components/SplashScreen";

export function SplashWrapper({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isAuthRoute = pathname === "/auth" || pathname === "/login";

  // `mounted` prevents any SSR/client mismatch — server always renders fully visible.
  const [mounted, setMounted] = useState(false);
  const [state, setState] = useState<"loading" | "splash" | "done">("done");

  useEffect(() => {
    setMounted(true);
    if (isAuthRoute) {
      setState("done");
      return;
    }
    const seen = sessionStorage.getItem("stocksense_splash_seen");
    setState(seen ? "done" : "splash");
  }, [isAuthRoute]);

  const handleDone = useCallback(() => {
    sessionStorage.setItem("stocksense_splash_seen", "1");
    setState("done");
  }, []);

  if (isAuthRoute) {
    return <>{children}</>;
  }

  // Before mount: render children fully visible (matches server HTML exactly).
  if (!mounted) {
    return <>{children}</>;
  }

  return (
    <>
      {state === "splash" && <SplashScreen onDone={handleDone} />}
      <div
        aria-hidden={state !== "done"}
        style={{
          visibility: state === "splash" ? "hidden" : "visible",
          opacity: state === "done" ? 1 : 0,
          transition: state === "done" ? "opacity 0.7s ease 0.15s" : "none",
        }}
      >
        {children}
      </div>
    </>
  );
}
