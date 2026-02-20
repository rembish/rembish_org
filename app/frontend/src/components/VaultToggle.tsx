import { useCallback, useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import { BiLock, BiLockOpen } from "react-icons/bi";
import { useAuth } from "../hooks/useAuth";
import { apiFetch } from "../lib/api";

export default function VaultToggle() {
  const { user } = useAuth();
  const { pathname } = useLocation();
  const [unlocked, setUnlocked] = useState<boolean | null>(null);

  const checkStatus = useCallback(() => {
    apiFetch("/api/auth/vault/status")
      .then((r) => r.json())
      .then((data) => setUnlocked(data.unlocked === true))
      .catch(() => setUnlocked(false));
  }, []);

  useEffect(() => {
    if (user?.is_admin && pathname.startsWith("/admin")) {
      checkStatus();
    } else {
      setUnlocked(null);
    }
  }, [user, pathname, checkStatus]);

  // Listen for vault status changes from auto-lock timer or other tabs
  useEffect(() => {
    const onVaultChange = () => checkStatus();
    window.addEventListener("vault-status-changed", onVaultChange);
    return () =>
      window.removeEventListener("vault-status-changed", onVaultChange);
  }, [checkStatus]);

  if (!user?.is_admin || !pathname.startsWith("/admin") || unlocked === null) {
    return null;
  }

  const handleClick = async () => {
    if (unlocked) {
      await apiFetch("/api/auth/vault/lock", { method: "POST" });
      setUnlocked(false);
      window.dispatchEvent(new CustomEvent("vault-status-changed"));
    } else {
      const redirect = encodeURIComponent(pathname);
      window.location.href = `/api/auth/vault/login?redirect=${redirect}`;
    }
  };

  return (
    <button
      type="button"
      className="vault-toggle"
      onClick={handleClick}
      title={unlocked ? "Lock vault" : "Unlock vault"}
    >
      {unlocked ? <BiLockOpen /> : <BiLock />}
    </button>
  );
}
