import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Singapore Visitor Pulse",
  description: "A public-data outlook for Singapore visitor pressure, model backtests, source-market forecasts and national holidays.",
  openGraph: { title: "Singapore Visitor Pulse", description: "How busy will Singapore feel? Explore the next 12 months.", images: ["/og.png"] },
  twitter: { card: "summary_large_image", title: "Singapore Visitor Pulse", description: "A public-data outlook for Singapore visitor pressure.", images: ["/og.png"] },
};
export default function RootLayout({children}:{children:React.ReactNode}){return <html lang="en"><body>{children}</body></html>}
