import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  title: "UDX Soluções de Pagamentos",
  description: "Plataforma empresarial de pagamentos e recebimentos UDX.",
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="pt-BR">
      <body style={{ margin: 0, background: "#090909", color: "#ffffff", fontFamily: "Arial, sans-serif" }}>
        {children}
      </body>
    </html>
  );
}
