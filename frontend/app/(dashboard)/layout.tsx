"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/components/auth/AuthProvider";
import { useTheme } from "@/components/shared/ThemeProvider";
import {
  Lightbulb,
  LayoutDashboard,
  LogOut,
  Menu,
  Moon,
  Plus,
  Settings,
  Sun,
  Grid3X3,
} from "lucide-react";
import { useState } from "react";

const sidebarLinks = [
  { href: "/ideas", label: "Idea Bank", icon: Lightbulb },
  { href: "/content-grid", label: "Content Grid", icon: Grid3X3 },
  { href: "/posts/new", label: "New Post", icon: Plus },
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/settings/strategy", label: "Settings", icon: Settings },
];

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const { theme, toggle } = useTheme();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="flex min-h-screen">
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 flex w-64 flex-col border-r border-border bg-card transition-transform lg:static lg:translate-x-0 ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex h-14 items-center border-b border-border px-4">
          <Link href="/ideas" className="text-lg font-bold text-primary">
            SMM
          </Link>
        </div>

        <nav className="flex-1 space-y-1 p-3">
          {sidebarLinks.map((link) => {
            const Icon = link.icon;
            const active = pathname.startsWith(link.href);
            return (
              <Link
                key={link.href}
                href={link.href}
                onClick={() => setSidebarOpen(false)}
                className={`flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                  active
                    ? "bg-primary/10 text-primary"
                    : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                }`}
              >
                <Icon size={18} />
                {link.label}
              </Link>
            );
          })}
        </nav>

        <div className="border-t border-border p-3">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <div className="flex-1 truncate">{user?.email}</div>
            <button
              onClick={toggle}
              className="rounded-md p-1.5 hover:bg-accent"
              title="Toggle theme"
            >
              {theme === "dark" ? <Sun size={16} /> : <Moon size={16} />}
            </button>
            <button
              onClick={logout}
              className="rounded-md p-1.5 hover:bg-accent"
              title="Sign out"
            >
              <LogOut size={16} />
            </button>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <div className="flex flex-1 flex-col">
        {/* Top bar (mobile) */}
        <header className="flex h-14 items-center gap-4 border-b border-border bg-card px-4 lg:hidden">
          <button onClick={() => setSidebarOpen(true)}>
            <Menu size={20} />
          </button>
          <span className="font-semibold">Social Media Manager</span>
        </header>

        <main className="flex-1 p-4 lg:p-6">{children}</main>
      </div>
    </div>
  );
}
