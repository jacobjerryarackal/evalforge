import React from "react";

interface CardProps {
  children: React.ReactNode;
  style?: React.CSSProperties;
}

export function Card({ children, style }: CardProps) {
  return (
    <div
      style={{
        background: "rgba(17, 24, 39, 0.6)",
        backdropFilter: "blur(10px)",
        border: "1px solid #1F2937",
        borderRadius: "0.75rem",
        padding: "1.5rem",
        ...style,
      }}
    >
      {children}
    </div>
  );
}
