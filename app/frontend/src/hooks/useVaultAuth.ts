import { useCallback, useEffect, useRef, useState } from "react";
import { apiFetch } from "../lib/api";

export function useVaultAuth() {
  const [unlocked, setUnlocked] = useState(false);
  const [loading, setLoading] = useState(true);
  const lockTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const checkStatus = useCallback(() => {
    apiFetch("/api/auth/vault/status")
      .then((res) => res.json())
      .then((data) => {
        setUnlocked(data.unlocked);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  const vaultFetch = useCallback(async (url: string, opts?: RequestInit) => {
    const res = await apiFetch(url, opts);
    if (res.status === 401) {
      const data = await res.json().catch(() => null);
      if (data?.detail === "vault_locked") {
        setUnlocked(false);
        window.dispatchEvent(new CustomEvent("vault-status-changed"));
        return null;
      }
    }
    return res;
  }, []);

  useEffect(() => {
    checkStatus();
  }, [checkStatus]);

  // Auto-lock timer: 10 min
  useEffect(() => {
    if (unlocked) {
      if (lockTimerRef.current) clearTimeout(lockTimerRef.current);
      lockTimerRef.current = setTimeout(() => {
        setUnlocked(false);
        window.dispatchEvent(new CustomEvent("vault-status-changed"));
      }, 600_000);
    }
    return () => {
      if (lockTimerRef.current) clearTimeout(lockTimerRef.current);
    };
  }, [unlocked]);

  // Listen for vault status changes from header toggle
  useEffect(() => {
    const onVaultChange = () => checkStatus();
    window.addEventListener("vault-status-changed", onVaultChange);
    return () =>
      window.removeEventListener("vault-status-changed", onVaultChange);
  }, [checkStatus]);

  return { unlocked, loading, vaultFetch };
}
