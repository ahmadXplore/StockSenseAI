"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";

export default function LoginPage() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/auth");
  }, [router]);

  return (
    <div className="flex items-center justify-center py-20 text-gray-400 text-sm">
      <Loader2 className="h-5 w-5 animate-spin mr-2 text-brand" /> Redirecting to Biometric Face Gateway…
    </div>
  );
}
