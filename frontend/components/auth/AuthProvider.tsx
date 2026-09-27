"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { getApi, ApiError } from "@/lib/api";

interface AuthUser {
  id: string;
  email: string;
}

interface AuthContextValue {
  user: AuthUser | null;
  profile: Record<string, unknown> | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue>({
  user: null,
  profile: null,
  loading: true,
  login: async () => {},
  register: async () => {},
  logout: () => {},
});

function setSessionCookie(token: string) {
  if (typeof document === "undefined") return;
  document.cookie = `session_token=${token}; path=/; max-age=${60 * 60 * 24 * 7}; SameSite=Lax`;
}

function clearSessionCookie() {
  if (typeof document === "undefined") return;
  document.cookie = "session_token=; path=/; max-age=0";
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [profile, setProfile] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(true);

  const checkSession = useCallback(async () => {
    try {
      const token = localStorage.getItem("session_token");
      if (!token) {
        setUser(null);
        setProfile(null);
        return;
      }
      const api = getApi();
      const session = await api.getSession();
      setUser(session.user as unknown as AuthUser);
      setProfile(session.profile);
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        localStorage.removeItem("session_token");
        clearSessionCookie();
      }
      setUser(null);
      setProfile(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    checkSession();
  }, [checkSession]);

  const login = async (email: string, password: string) => {
    const api = getApi();
    const res = await api.login(email, password);
    localStorage.setItem("session_token", res.session_token);
    setSessionCookie(res.session_token);
    const session = await api.getSession();
    setUser(session.user as unknown as AuthUser);
    setProfile(session.profile);
  };

  const register = async (email: string, password: string) => {
    const api = getApi();
    await api.register(email, password);
  };

  const logout = () => {
    localStorage.removeItem("session_token");
    clearSessionCookie();
    setUser(null);
    setProfile(null);
  };

  return (
    <AuthContext.Provider value={{ user, profile, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
