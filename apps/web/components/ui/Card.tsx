interface CardProps {
  children: React.ReactNode;
  accent?: "green" | "gold" | "orange" | "divider" | "none";
  hover?: boolean;
  className?: string;
}

const accentClasses = {
  green: "border-l-[3px] border-l-zil-green",
  gold: "border-l-[3px] border-l-zil-gold",
  orange: "border-l-[3px] border-l-zil-orange",
  divider: "border-l-[3px] border-l-zil-divider",
  none: "",
};

export function Card({
  children,
  accent = "none",
  hover = false,
  className = "",
}: CardProps) {
  return (
    <div
      className={[
        "p-4 md:p-5",
        accentClasses[accent],
        hover ? "hover:bg-zil-card transition-colors" : "",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
    >
      {children}
    </div>
  );
}
