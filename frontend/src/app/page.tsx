"use client";

import { useEffect, useState } from "react";
import { fetchHealth, HealthStatus } from "@/lib/api";

export default function Home() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchHealth()
      .then((data) => {
        setHealth(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message || "Failed to connect to backend");
        setLoading(false);
      });
  }, []);

  return (
    <main className="min-h-screen bg-neutral-50 text-neutral-900 flex flex-col items-center justify-center p-6">
      <div className="max-w-xl w-full bg-white border border-neutral-200 rounded-lg p-8 shadow-sm">
        <div className="mb-6">
          <span className="text-xs font-semibold tracking-wider uppercase text-neutral-500">
            Phase 0 Foundation
          </span>
          <h1 className="text-2xl font-bold tracking-tight text-neutral-900 mt-1">
            GlobalTrade.ai
          </h1>
          <p className="text-sm text-neutral-600 mt-1">
            AI-assisted global import-export operating platform.
          </p>
        </div>

        <div className="border-t border-neutral-100 pt-6">
          <h2 className="text-sm font-semibold text-neutral-800 mb-3">
            System &amp; Connectivity Status
          </h2>

          {loading && (
            <div className="flex items-center space-x-2 text-sm text-neutral-500">
              <span className="inline-block w-2 h-2 rounded-full bg-amber-400 animate-pulse"></span>
              <span>Checking backend API connection...</span>
            </div>
          )}

          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded text-sm text-red-700">
              <strong>Connection Error:</strong> {error}
            </div>
          )}

          {health && (
            <div className="space-y-3 text-sm">
              <div className="flex justify-between items-center py-1 border-b border-neutral-100">
                <span className="text-neutral-500">Overall Status</span>
                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-emerald-100 text-emerald-800">
                  {health.status}
                </span>
              </div>
              <div className="flex justify-between items-center py-1 border-b border-neutral-100">
                <span className="text-neutral-500">Backend API</span>
                <span className="font-mono text-xs text-neutral-800">
                  {health.project} ({health.environment})
                </span>
              </div>
              <div className="flex justify-between items-center py-1 border-b border-neutral-100">
                <span className="text-neutral-500">PostgreSQL (psycopg v3)</span>
                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-emerald-100 text-emerald-800">
                  {health.database.status}
                </span>
              </div>
              <div className="flex justify-between items-center py-1">
                <span className="text-neutral-500">pgvector Extension</span>
                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-emerald-100 text-emerald-800">
                  {health.database.pgvector}
                </span>
              </div>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
