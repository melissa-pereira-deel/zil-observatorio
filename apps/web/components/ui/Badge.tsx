type BadgeVariant = "green" | "gold" | "orange" | "muted" | "outline";

interface BadgeProps {
  children: React.ReactNode;
  variant?: BadgeVariant;
  className?: string;
}

const variantClasses: Record<BadgeVariant, string> = {
  green: "bg-zil-green-light text-zil-green border-zil-green/20",
  gold: "bg-zil-gold-light text-zil-gold-dark border-zil-gold/20",
  orange: "bg-zil-orange-light text-zil-orange border-zil-orange/20",
  muted: "bg-zil-card text-zil-muted border-zil-divider",
  outline: "bg-transparent text-zil-soft border-zil-divider",
};

export function Badge({
  children,
  variant = "green",
  className = "",
}: BadgeProps) {
  return (
    <span
      className={[
        "inline-flex items-center px-2.5 py-0.5 text-xs font-mono tracking-wider border",
        variantClasses[variant],
        className,
      ]
        .filter(Boolean)
        .join(" ")}
    >
      {children}
    </span>
  );
}
