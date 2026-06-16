import type { Metadata, Viewport } from "next";
import { AuthGate } from "@/features/auth/components/auth-gate";
import "./globals.css";

export const metadata: Metadata = {
  title: "EdgeVault AI",
  description: "Upload, manage, and ask questions about finance documents.",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
  themeColor: "#f7f8fb",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full flex flex-col">
        <AuthGate>{children}</AuthGate>
      </body>
    </html>
  );
}
