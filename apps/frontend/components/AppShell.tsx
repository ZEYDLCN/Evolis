import { ReactNode } from "react";
import Sidebar from "./Sidebar";
import BottomNav from "./BottomNav";
import CommandPalette from "./CommandPalette";

/** Wraps every authenticated page: desktop gets a fixed left sidebar,
 * mobile gets a bottom tab bar — replacing the old top NavBar everywhere. */
export default function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-surface">
      <Sidebar />
      <main className="mx-auto max-w-4xl px-4 pb-20 pt-6 md:pb-10 md:pl-64 md:pr-6">{children}</main>
      <BottomNav />
      <CommandPalette />
    </div>
  );
}
