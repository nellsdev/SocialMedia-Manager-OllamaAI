import type { Metadata } from "next";
import { AuthProvider } from "@/components/auth/AuthProvider";
import { ThemeProvider } from "@/components/shared/ThemeProvider";
import "./globals.css";

export const metadata: Metadata = {
  title: "Social Media Manager",
  description: "Multi-persona social media content planning and AI-assisted publishing",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="min-h-screen bg-background font-sans antialiased">
        <ThemeProvider>
          <AuthProvider>
            {children}
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
