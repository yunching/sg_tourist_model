import type { Metadata } from "next";
import "./globals.css";

const repositoryName = process.env.GITHUB_REPOSITORY?.split("/")[1] ?? "sg_tourist_model";
const basePath = process.env.GITHUB_PAGES === "true" ? `/${repositoryName}` : "";
const socialImage = `${basePath}/og.png`;

const siteOrigin = process.env.GITHUB_PAGES === "true"
  ? "https://yunching.github.io"
  : "https://singapore-visitor-pulse.yclim.chatgpt.site";

export const metadata: Metadata = {
  metadataBase: new URL(siteOrigin),
  title: "Singapore Visitor Pulse",
  description: "A public-data outlook for Singapore visitor pressure, model backtests, source-market forecasts and national holidays.",
  openGraph: { title: "Singapore Visitor Pulse", description: "How busy will Singapore feel? Explore the next 12 months.", images: [socialImage] },
  twitter: { card: "summary_large_image", title: "Singapore Visitor Pulse", description: "A public-data outlook for Singapore visitor pressure.", images: [socialImage] },
};
export default function RootLayout({children}:{children:React.ReactNode}){return <html lang="en"><body>{children}</body></html>}
