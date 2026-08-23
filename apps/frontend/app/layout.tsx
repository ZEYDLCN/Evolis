import { brand } from "../lib/styles";

export const metadata = {
  title: "Evolis — Personal Evolution Intelligence",
  description: "AI-powered personal evolution analytics.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body style={{ fontFamily: "system-ui, sans-serif", margin: 0, background: brand.surfaceTint, color: brand.deepForest }}>
        {children}
      </body>
    </html>
  );
}
