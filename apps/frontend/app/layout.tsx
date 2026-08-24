import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-sans" });

export const metadata = {
  title: "Evolis — Personal Evolution Intelligence",
  description: "AI-powered personal evolution analytics.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="m-0 font-sans">{children}</body>
    </html>
  );
}
