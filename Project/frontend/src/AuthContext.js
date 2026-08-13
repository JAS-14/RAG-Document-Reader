import React, { createContext, useContext, useState } from "react";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  // Deliberately NOT read from localStorage/sessionStorage on init. This is
  // what makes every full page refresh land back on the login page: any
  // in-memory React state resets to its initial value on reload, so `token`
  // starts as null again every time, regardless of how recently the user
  // logged in. If you ever want "stay logged in across refresh" instead,
  // the fix is to read localStorage.getItem("token") here on mount -- but
  // that's the opposite of what was asked for.
  const [token, setToken] = useState(null);

  const login = (newToken) => setToken(newToken);
  const logout = () => setToken(null);

  return (
    <AuthContext.Provider value={{ token, isAuthenticated: !!token, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return ctx;
}