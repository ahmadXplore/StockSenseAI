"use client";

import { useState, useCallback, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  ShieldCheck, Lock, UserPlus, ArrowRight, Eye, EyeOff,
  Check, Loader2, KeyRound, AlertCircle,
} from "lucide-react";
import { api } from "@/lib/api";

function PinDots({ length, filled }: { length: number; filled: number }) {
  return (
    <div className="flex items-center justify-center gap-3 my-2">
      {Array.from({ length }).map((_, i) => (
        <div
          key={i}
          className={`w-3.5 h-3.5 rounded-full border-2 transition-all duration-200 ${
            i < filled ? "bg-brand border-brand scale-110" : "bg-transparent border-white/30"
          }`}
        />
      ))}
    </div>
  );
}

function SuccessOverlay({ userName, step }: { userName: string; step: number }) {
  return (
    <div className="fixed inset-0 z-50 bg-[#060912] flex flex-col items-center justify-center text-center p-6">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_40%,rgba(59,130,246,0.18),transparent_70%)] pointer-events-none" />
      <div className="relative z-10 max-w-sm w-full space-y-6">
        <div className="relative inline-flex items-center justify-center">
          <div className="w-20 h-20 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 shadow-2xl shadow-emerald-500/20">
            <ShieldCheck className="w-10 h-10 animate-bounce" />
          </div>
          <div className="absolute -inset-2 rounded-3xl bg-emerald-500/20 blur-xl -z-10 animate-pulse" />
        </div>
        <div className="space-y-1.5">
          <h2 className="text-2xl font-bold text-white tracking-tight">Access Granted</h2>
          <p className="text-sm text-gray-400">Welcome back, <span className="text-white font-semibold">{userName}</span></p>
        </div>
        <div className="bg-white/5 border border-white/10 rounded-xl p-4 text-left space-y-2 font-mono text-xs">
          {["PIN credentials verified", "Decrypting market stream keys", "Loading quantitative models", "Redirecting to terminal…"].map((label, i) => (
            <div key={i} className={`flex items-center gap-2 transition-colors duration-300 ${step > i ? "text-emerald-400" : "text-gray-600"}`}>
              {step > i ? <Check className="h-3.5 w-3.5 shrink-0" /> : <div className="h-3.5 w-3.5 rounded-full border border-gray-700 shrink-0" />}
              <span>{label}</span>
            </div>
          ))}
        </div>
        <div className="w-full bg-white/5 rounded-full h-1.5 overflow-hidden">
          <div className="bg-brand h-full transition-all duration-500 ease-out" style={{ width: `${(step / 4) * 100}%` }} />
        </div>
      </div>
    </div>
  );
}

export default function AuthPage() {
  const router = useRouter();
  const [mode, setMode] = useState<"login" | "signup">("login");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [pin, setPin] = useState("");
  const [confirmPin, setConfirmPin] = useState("");

  const [showPin, setShowPin] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [transition, setTransition] = useState<{ user: string; step: number } | null>(null);

  useEffect(() => {
    setError(null); setSuccess(null); setPin(""); setConfirmPin("");
  }, [mode]);

  const triggerSuccess = useCallback((userName: string, token: string, userObj: any) => {
    if (typeof window !== "undefined") {
      sessionStorage.setItem("stocksense_auth_token", token || "");
      sessionStorage.setItem("stocksense_user", JSON.stringify(userObj));
      sessionStorage.setItem("stocksense_splash_seen", "1");
    }
    setTransition({ user: userName, step: 1 });
    setTimeout(() => setTransition(p => p ? { ...p, step: 2 } : null), 600);
    setTimeout(() => setTransition(p => p ? { ...p, step: 3 } : null), 1300);
    setTimeout(() => setTransition(p => p ? { ...p, step: 4 } : null), 2000);
    setTimeout(() => router.push("/dashboard"), 2600);
  }, [router]);

  const handleLogin = useCallback(async () => {
    setError(null);
    if (!name.trim()) { setError("Please enter your name."); return; }
    if (!pin) { setError("Please enter your PIN."); return; }
    setLoading(true);
    try {
      const res = await api.auth.pinLogin({ identifier: name.trim(), pin });
      if (res.success && res.user) {
        triggerSuccess(res.user.name, res.token || "", res.user);
      } else {
        setError(res.message || "Incorrect name or PIN.");
      }
    } catch (e: any) {
      setError(e.message || "Server error. Please try again.");
    } finally {
      setLoading(false);
    }
  }, [name, pin, triggerSuccess]);

  const handleSignup = useCallback(async () => {
    setError(null);
    if (!name.trim()) { setError("Please enter your full name."); return; }
    if (pin.length < 4) { setError("PIN must be at least 4 characters."); return; }
    if (pin !== confirmPin) { setError("PINs do not match."); return; }
    setLoading(true);
    try {
      const res = await api.auth.lanSignup({
        name: name.trim(),
        email: email.trim() || undefined,
        role: "user",
        pin,
      });
      if (res.success && res.user) {
        const newUser = res.user;
        setSuccess(`Account created! Signing you in as ${newUser.name}…`);
        setTimeout(() => triggerSuccess(newUser.name, res.token || "", newUser), 800);
      } else {
        setError(res.message || "Signup failed. Please try again.");
      }
    } catch (e: any) {
      setError(e.message || "Server error. Please try again.");
    } finally {
      setLoading(false);
    }
  }, [name, email, pin, confirmPin, triggerSuccess]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !loading) mode === "login" ? handleLogin() : handleSignup();
  };

  if (transition) return <SuccessOverlay userName={transition.user} step={transition.step} />;

  return (
    <div className="min-h-screen bg-[#060912] flex flex-col" onKeyDown={handleKeyDown}>
      <div className="fixed inset-0 pointer-events-none">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[400px] bg-brand/10 rounded-full blur-[120px]" />
        <div className="absolute bottom-0 right-1/4 w-[400px] h-[300px] bg-purple-600/8 rounded-full blur-[100px]" />
      </div>

      <div className="relative z-10 flex flex-1 items-center justify-center p-4">
        <div className="w-full max-w-md">
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-brand/10 border border-brand/20 mb-4 shadow-lg shadow-brand/10">
              <KeyRound className="w-8 h-8 text-brand" />
            </div>
            <h1 className="text-2xl font-bold text-white tracking-tight">StockSense AI</h1>
            <p className="text-sm text-gray-400 mt-1">Secure PIN authentication</p>
          </div>

          <div className="flex rounded-xl bg-white/5 border border-white/10 p-1 mb-6">
            {(["login", "signup"] as const).map(m => (
              <button
                key={m}
                onClick={() => setMode(m)}
                className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 ${
                  mode === m ? "bg-brand text-white shadow-lg shadow-brand/30" : "text-gray-400 hover:text-white"
                }`}
              >
                {m === "login" ? <><Lock className="h-4 w-4" /> Sign In</> : <><UserPlus className="h-4 w-4" /> Create Account</>}
              </button>
            ))}
          </div>

          <div className="bg-white/[0.04] border border-white/10 rounded-2xl p-6 backdrop-blur-sm space-y-4 shadow-2xl">
            {/* Name */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-gray-400 uppercase tracking-wider">{mode === "login" ? "Name or Email" : "Full Name"}</label>
              <input type="text" value={name} onChange={e => { setName(e.target.value); setError(null); }}
                placeholder={mode === "login" ? "Enter your name…" : "Enter your full name…"}
                className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-gray-600 text-sm focus:outline-none focus:border-brand/50 focus:ring-1 focus:ring-brand/30 transition-all"
                autoFocus />
            </div>

            {/* Email (signup) */}
            {mode === "signup" && (
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Email <span className="normal-case font-normal text-gray-600">(optional)</span></label>
                <input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="your@email.com"
                  className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-gray-600 text-sm focus:outline-none focus:border-brand/50 focus:ring-1 focus:ring-brand/30 transition-all" />
              </div>
            )}

            {/* PIN */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-gray-400 uppercase tracking-wider">{mode === "login" ? "Your PIN" : "Choose a PIN"}</label>
              <div className="relative">
                <input type={showPin ? "text" : "password"} value={pin} onChange={e => { setPin(e.target.value); setError(null); }}
                  placeholder={mode === "login" ? "Enter your PIN…" : "Min. 4 characters…"}
                  className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 pr-11 text-white placeholder-gray-600 text-sm focus:outline-none focus:border-brand/50 focus:ring-1 focus:ring-brand/30 transition-all" />
                <button type="button" onClick={() => setShowPin(v => !v)} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300 transition-colors">
                  {showPin ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
              {mode === "signup" && pin.length > 0 && <PinDots length={Math.max(4, pin.length)} filled={pin.length} />}
            </div>

            {/* Confirm PIN (signup) */}
            {mode === "signup" && (
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Confirm PIN</label>
                <div className="relative">
                  <input type={showConfirm ? "text" : "password"} value={confirmPin} onChange={e => { setConfirmPin(e.target.value); setError(null); }}
                    placeholder="Re-enter your PIN…"
                    className={`w-full bg-white/5 border rounded-xl px-4 py-3 pr-11 text-white placeholder-gray-600 text-sm focus:outline-none focus:ring-1 transition-all ${
                      confirmPin && confirmPin !== pin ? "border-red-500/50 focus:ring-red-500/30" : confirmPin && confirmPin === pin ? "border-emerald-500/50 focus:ring-emerald-500/30" : "border-white/10 focus:border-brand/50 focus:ring-brand/30"
                    }`} />
                  <button type="button" onClick={() => setShowConfirm(v => !v)} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300 transition-colors">
                    {showConfirm ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
                {confirmPin && confirmPin === pin && <p className="text-emerald-400 text-xs flex items-center gap-1"><Check className="h-3 w-3" /> PINs match</p>}
              </div>
            )}



            {/* Messages */}
            {error && (
              <div className="flex items-start gap-2 bg-red-500/10 border border-red-500/20 text-red-400 text-sm rounded-xl px-4 py-3">
                <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />{error}
              </div>
            )}
            {success && (
              <div className="flex items-start gap-2 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm rounded-xl px-4 py-3">
                <Check className="h-4 w-4 shrink-0 mt-0.5" />{success}
              </div>
            )}

            {/* Submit */}
            <button onClick={mode === "login" ? handleLogin : handleSignup} disabled={loading}
              className="w-full flex items-center justify-center gap-2 bg-brand hover:bg-brand/90 disabled:opacity-60 disabled:cursor-not-allowed text-white font-semibold py-3 rounded-xl transition-all duration-200 shadow-lg shadow-brand/30 hover:shadow-brand/50 hover:scale-[1.01] active:scale-[0.99]">
              {loading ? <><Loader2 className="h-4 w-4 animate-spin" /> Processing…</> :
                mode === "login" ? <><Lock className="h-4 w-4" /> Sign In <ArrowRight className="h-4 w-4" /></> :
                  <><UserPlus className="h-4 w-4" /> Create Account <ArrowRight className="h-4 w-4" /></>}
            </button>
          </div>

          <p className="text-center text-sm text-gray-500 mt-5">
            {mode === "login" ? "Don't have an account? " : "Already have an account? "}
            <button onClick={() => setMode(mode === "login" ? "signup" : "login")} className="text-brand hover:text-brand/80 font-medium transition-colors">
              {mode === "login" ? "Create one" : "Sign in"}
            </button>
          </p>


        </div>
      </div>
    </div>
  );
}
