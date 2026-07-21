"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { getApi } from "@/lib/api";

interface AuthUser {
  id: string;
  email: string;
}

interface AuthContextValue {
  user: AuthUser | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue>({
  user: null,
  loading: true,
  login: async () => {},
  register: async () => {},
  logout: () => {},
});

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  const checkSession = useCallback(async () => {
    try {
      const token = localStorage.getItem("session_token");
      if (!token) {
        setUser(null);
        return;
      }
      const api = getApi();
      const session = await api.getSession();
      setUser(session.user as AuthUser);
    } catch {
      localStorage.removeItem("session_token");
      setUser(null);
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
    setUser({ id: res.user_id, email });
  };

  const register = async (email: string, password: string) => {
    const api = getApi();
    await api.register(email, password);
  };

  const logout = () => {
    localStorage.removeItem("session_token");
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
