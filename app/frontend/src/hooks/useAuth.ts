import {
  createContext,
  createElement,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { apiFetch } from "../lib/api";

interface User {
  id: number;
  email: string;
  name: string | null;
  nickname: string | null;
  picture: string | null;
  birthday: string | null;
  is_admin: boolean;
}

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  login: () => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiFetch("/api/auth/me")
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
    apiFetch("/api/auth/logout", { method: "POST" }).then(() => {
      window.location.href = "/";
    });
  };

  return createElement(
    AuthContext.Provider,
    { value: { user, loading, login, logout } },
    children,
  );
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
