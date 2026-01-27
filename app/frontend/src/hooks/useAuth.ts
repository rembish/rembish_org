import { useState, useEffect } from "react";

interface User {
  id: number;
  email: string;
  name: string | null;
  nickname: string | null;
  picture: string | null;
  birthday: string | null;
  is_admin: boolean;
}

export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/auth/me", { credentials: "include" })
      .then((res) => res.json())
      .then((data) => {
        setUser(data);
        setLoading(false);
      })
      .catch(() => {
        setUser(null);
        setLoading(false);
      });
  }, []);

  const login = () => {
    const redirect = encodeURIComponent(window.location.pathname);
    window.location.href = `/api/auth/login?redirect=${redirect}`;
  };

  const logout = () => {
    const redirect = encodeURIComponent(window.location.pathname);
    window.location.href = `/api/auth/logout?redirect=${redirect}`;
  };

  return { user, loading, login, logout };
}
