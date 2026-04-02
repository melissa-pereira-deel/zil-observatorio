interface CalloutProps {
  children: React.ReactNode;
  variant?: "dark" | "light" | "card";
  className?: string;
}

const variantClasses = {
  dark: "bg-zil-green-dark text-zil-bg",
  light: "bg-zil-card border-l-[3px] border-l-zil-gold",
  card: "bg-zil-card",
};

export function Callout({
  children,
  variant = "light",
  className = "",
}: CalloutProps) {
  return (
    <div
      className={[
        "p-4 md:p-5",
        variantClasses[variant],
        className,
      ]
        .filter(Boolean)
        .join(" ")}
    >
      {children}
    </div>
  );
}
