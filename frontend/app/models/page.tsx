"use client";

import { useEffect, useState } from "react";
import { Brain, CheckCircle, Clock, AlertTriangle, RefreshCw, Loader2, BarChart3 } from "lucide-react";
import { api, ModelMetadata } from "@/lib/api";
import Link from "next/link";

function MetricBadge({ label, value }: { label: string; value: number }) {
  return (
    <div className="bg-background rounded px-2 py-1 text-center">
      <div className="text-[9px] text-gray-500">{label}</div>
      <div className="text-xs font-mono font-bold text-white">{(value * 100).toFixed(1)}%</div>
    </div>
  );
}

const STATUS_STYLES: Record<string, { color: string; icon: React.ElementType }> = {
  DEPLOYED:   { color: "text-emerald-400", icon: CheckCircle },
  STAGED:     { color: "text-blue-400",    icon: Clock },
  ARCHIVED:   { color: "text-gray-500",    icon: Clock },
  DEPRECATED: { color: "text-red-400",     icon: AlertTriangle },
};

import { BackButton } from "@/components/BackButton";

export default function ModelsPage() {
  const [models, setModels] = useState<ModelMetadata[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [refreshing, setRefreshing] = useState(false);

  const fetchModels = async (isRetry = false) => {
    setLoading(true);
    setError("");
    try {
      const data = await api.ml.models();
      setModels(Array.isArray(data) ? data : []);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      // Ignore abort/interrupt errors caused by StrictMode or navigation
      if (msg.toLowerCase().includes("abort") || msg.toLowerCase().includes("interrupt")) {
        if (!isRetry) {
          // Retry once
          setTimeout(() => fetchModels(true), 800);
          return;
        }
        setError("");
        setModels([]);
      } else {
        setError(msg || "Could not load models. Is the backend running?");
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const timer = setTimeout(() => fetchModels(), 100);
    return () => clearTimeout(timer);
  }, []);

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchModels();
    setRefreshing(false);
  };

  const deployed = models.filter(m => m.is_deployed);
  const staged   = models.filter(m => !m.is_deployed);

  return (
    <div className="space-y-6 py-4">
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-border/60 pb-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <BackButton fallbackHref="/dashboard" label="Back to Dashboard" />
            <span className="text-xs font-mono text-brand font-semibold uppercase">AI Center</span>
          </div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Brain className="h-5 w-5 text-brand" /> ML Model Registry &amp; Health
          </h1>
          <p className="text-xs text-gray-400">Deployed XGBoost, LightGBM, and LSTM neural ensemble models with walk-forward validation metrics.</p>
        </div>
        <button onClick={handleRefresh} disabled={loading || refreshing}
          className="flex items-center gap-1.5 px-3 py-2 bg-background-elevated border border-border rounded-lg text-xs text-gray-300 hover:text-white transition-colors">
          <RefreshCw className={`h-3.5 w-3.5 ${refreshing ? "animate-spin" : ""}`} /> Refresh
        </button>
      </div>

      {/* Summary */}
      {!loading && (
        <div className="grid grid-cols-3 gap-4">
          {[
            { label: "Total Models", value: models.length.toString() },
            { label: "Deployed", value: deployed.length.toString() },
            { label: "Staged", value: staged.length.toString() },
          ].map(({ label, value }) => (
            <div key={label} className="bg-background-elevated border border-border rounded-xl p-4 text-center">
              <div className="text-2xl font-bold font-mono text-white">{value}</div>
              <div className="text-xs text-gray-400 mt-1">{label}</div>
            </div>
          ))}
        </div>
      )}

      {error && (
        <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-4 text-sm text-red-400">
          {error}
        </div>
      )}

      {/* Train a new model CTA */}
      <div className="bg-brand/5 border border-brand/20 rounded-xl p-5 flex items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="text-sm font-semibold text-white">Train a new model</div>
          <div className="text-xs text-gray-400">
            POST to <code className="font-mono text-brand bg-brand/10 px-1 rounded">/api/v1/ml/train</code> with{" "}
            <code className="font-mono text-brand bg-brand/10 px-1 rounded">security_id</code> and{" "}
            <code className="font-mono text-brand bg-brand/10 px-1 rounded">horizon</code>
          </div>
        </div>
        <a href="http://localhost:8000/docs#/Machine%20Learning/train_model_api_v1_ml_train_post"
          target="_blank" rel="noopener noreferrer"
          className="shrink-0 px-4 py-2 bg-brand hover:bg-brand-hover text-white rounded-lg text-xs font-semibold transition-colors">
          Open API Docs →
        </a>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20 text-gray-400">
          <Loader2 className="h-6 w-6 animate-spin mr-2" /> Loading model registry…
        </div>
      ) : models.length === 0 ? (
        <div className="bg-background-elevated border border-border rounded-xl p-12 text-center space-y-3">
          <Brain className="h-10 w-10 text-gray-600 mx-auto" />
          <div className="text-gray-400 text-sm">No models trained yet.</div>
          <p className="text-xs text-gray-600 max-w-sm mx-auto">
            Train your first model by calling POST /api/v1/ml/train with a security_id like{" "}
            <code className="font-mono text-brand">US::NASDAQ::AAPL</code> and horizon like{" "}
            <code className="font-mono text-brand">30d</code>.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {models.map((m) => {
            const style = STATUS_STYLES[m.status] ?? STATUS_STYLES.ARCHIVED;
            const StatusIcon = style.icon;
            return (
              <div key={m.model_id} className="bg-background-elevated border border-border rounded-xl p-5 space-y-4">
                {/* Header */}
                <div className="flex items-start justify-between gap-4 flex-wrap">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-white font-mono">{m.model_name}</span>
                      <span className={`flex items-center gap-1 text-[10px] font-bold px-1.5 py-0.5 rounded ${style.color} bg-current/10`}>
                        <StatusIcon className="h-2.5 w-2.5" />
                        {m.status}
                      </span>
                      {m.is_deployed && (
                        <span className="text-[10px] font-bold text-emerald-400 bg-emerald-500/10 px-1.5 py-0.5 rounded">LIVE</span>
                      )}
                    </div>
                    <div className="text-xs text-gray-400">
                      {m.market_code} · {m.exchange_code} · Horizon: <span className="font-mono text-white">{m.horizon}</span>
                    </div>
                    <div className="text-[10px] text-gray-500">
                      Feature version: {m.feature_version} · Created: {new Date(m.created_at).toLocaleDateString()}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-[10px] text-gray-500 mb-1">Model ID</div>
                    <code className="text-[10px] font-mono text-gray-400 bg-background px-2 py-0.5 rounded">
                      {m.model_id.slice(0, 16)}…
                    </code>
                  </div>
                </div>

                {/* Metrics */}
                {Object.keys(m.metrics ?? {}).length > 0 && (
                  <div className="space-y-2">
                    <div className="text-[10px] font-semibold text-gray-400">Validation Metrics</div>
                    <div className="flex gap-2 flex-wrap">
                      {m.metrics.accuracy !== undefined && <MetricBadge label="Accuracy" value={m.metrics.accuracy} />}
                      {m.metrics.brier_score !== undefined && <MetricBadge label="Brier Score" value={1 - m.metrics.brier_score} />}
                      {m.metrics.conformal_coverage !== undefined && <MetricBadge label="Conformal Cov." value={m.metrics.conformal_coverage} />}
                      {m.metrics.mae !== undefined && (
                        <div className="bg-background rounded px-2 py-1 text-center">
                          <div className="text-[9px] text-gray-500">MAE</div>
                          <div className="text-xs font-mono font-bold text-white">{m.metrics.mae.toFixed(4)}</div>
                        </div>
                      )}
                      {m.metrics.rmse !== undefined && (
                        <div className="bg-background rounded px-2 py-1 text-center">
                          <div className="text-[9px] text-gray-500">RMSE</div>
                          <div className="text-xs font-mono font-bold text-white">{m.metrics.rmse.toFixed(4)}</div>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Artifact hash */}
                {m.artifact_hash && (
                  <div className="text-[10px] text-gray-600 flex items-center gap-1.5">
                    <span>SHA-256:</span>
                    <code className="font-mono text-gray-500">{m.artifact_hash.slice(0, 32)}…</code>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
