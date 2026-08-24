import { Inter } from "next/font/google";
import "./globals.css";
import { THEME_INIT_SCRIPT } from "../lib/theme";
import { LangProvider } from "../components/LangProvider";

const inter = Inter({ subsets: ["latin"], variable: "--font-sans" });

export const metadata = {
  title: "Evolis — Personal Evolution Intelligence",
  description: "Evolis helps you understand how your skills, focus, habits, projects and interests evolve over time.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={inter.variable} suppressHydrationWarning>
      <head>
        {/* Sets the dark class before first paint so a returning dark-mode
         * user never sees a light flash (section 47). */}
        <script dangerouslySetInnerHTML={{ __html: THEME_INIT_SCRIPT }} />
      </head>
      <body className="m-0 font-sans" suppressHydrationWarning>
        <LangProvider>{children}</LangProvider>
      </body>
    </html>
  );
}
