/**
 * Badge — unified badge component.
 *
 * variant="category" — bordered, transparent bg (ZIL category tags)
 * variant="status"   — ● dot + label in mono (pipeline status)
 * variant="result"   — bold colored bg (APROVADO / REJEITADO)
 * variant="outline"  — neutral outline (default, replaces legacy color variants)
 */

type BadgeVariant = "category" | "status" | "result" | "outline";
type BadgeColor = "green" | "orange" | "gold" | "muted";

interface BadgeProps {
  children: React.ReactNode;
  variant?: BadgeVariant;
  color?: BadgeColor;
  className?: string;
  title?: string;
}

export function Badge({
  children,
  variant = "outline",
  color = "muted",
  className = "",
  title,
}: BadgeProps) {
  if (variant === "result") {
    const cls =
      color === "green"
        ? "bg-zil-green/10 text-zil-green"
        : color === "orange"
        ? "bg-zil-orange-light text-zil-orange"
        : color === "gold"
        ? "bg-zil-gold-light text-zil-gold-dark"
        : "bg-zil-card text-zil-muted";
    return (
      <span
        className={`font-mono text-xs font-semibold px-2 py-0.5 rounded-sm ${cls} ${className}`}
        title={title}
      >
        {children}
      </span>
    );
  }

  if (variant === "status") {
    const dotCls =
      color === "green"
        ? "bg-zil-green"
        : color === "orange"
        ? "bg-zil-orange"
        : color === "gold"
        ? "bg-zil-gold"
        : "bg-zil-muted";
    const textCls =
      color === "green"
        ? "text-zil-green border-zil-green/50"
        : color === "orange"
        ? "text-zil-orange border-zil-orange/50"
        : color === "gold"
        ? "text-zil-gold border-zil-gold/50"
        : "text-zil-muted border-zil-divider";
    return (
      <span
        className={`inline-flex items-center gap-1 font-mono text-xs px-2 py-0.5 border ${textCls} ${className}`}
        title={title}
      >
        <span className={`w-1.5 h-1.5 rounded-full inline-block shrink-0 ${dotCls}`} />
        {children}
      </span>
    );
  }

  if (variant === "category") {
    return (
      <span
        className={`inline-flex items-center gap-1 px-2 py-0.5 text-xs font-mono tracking-wider bg-zil-green/8 text-zil-green border border-zil-green/20 rounded-sm ${className}`}
        title={title}
      >
        {children}
      </span>
    );
  }

  // outline (default / legacy)
  const outlineCls =
    color === "green"
      ? "bg-zil-green-light text-zil-green border-zil-green/20"
      : color === "orange"
      ? "bg-zil-orange-light text-zil-orange border-zil-orange/20"
      : color === "gold"
      ? "bg-zil-gold-light text-zil-gold-dark border-zil-gold/20"
      : "bg-zil-card text-zil-muted border-zil-divider";
  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 text-xs font-mono tracking-wider border ${outlineCls} ${className}`}
      title={title}
    >
      {children}
    </span>
  );
}
