import React from "react";

export const metadata = {
  title: "EvalForge Platform",
  description: "AI Agent Evaluation Engine Dashboard",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body
        style={{
          fontFamily: "'Inter', sans-serif",
          margin: 0,
          backgroundColor: "#0B0F19",
          color: "#F3F4F6",
        }}
      >
        {children}
      </body>
    </html>
  );
}
