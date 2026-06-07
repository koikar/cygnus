import type { Metadata, Viewport } from "next";
import "./globals.css";

const title = "ReflexOS - AI-native training for robot workers";
const description =
  "ReflexOS exposes any robot arm as an MCP server so an AI agent can operate it, learn from its own failures, and turn successful attempts into reusable reflexes. Less teleoperation, less re-engineering.";

export const metadata: Metadata = {
  metadataBase: new URL("https://reflexos.dev"),
  title,
  description,
  keywords: [
    "ReflexOS",
    "robot training",
    "MCP server",
    "robot arm",
    "AI agent",
    "warehouse robotics",
    "sim-to-real",
    "cross-robot skill transfer",
  ],
  openGraph: {
    title,
    description,
    type: "website",
    siteName: "ReflexOS",
  },
  twitter: {
    card: "summary_large_image",
    title,
    description,
  },
};

export const viewport: Viewport = {
  themeColor: "#0d0f14",
  colorScheme: "dark",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="relative min-h-full bg-bg text-fg">
        <div aria-hidden className="fx-grid" />
        <div aria-hidden className="fx-noise" />
        <div className="relative z-10 flex min-h-[100dvh] flex-col">
          {children}
        </div>
      </body>
    </html>
  );
}
