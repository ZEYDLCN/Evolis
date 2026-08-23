export const metadata = {
  title: "LifeDiff — Version Control for Your Life",
  description: "AI-powered personal evolution analytics.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body style={{ fontFamily: "system-ui, sans-serif", margin: 0 }}>{children}</body>
    </html>
  );
}
