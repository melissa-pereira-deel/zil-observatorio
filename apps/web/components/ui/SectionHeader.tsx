interface SectionHeaderProps {
  number?: string;
  title: string;
  description?: string;
}

export function SectionHeader({ number, title, description }: SectionHeaderProps) {
  return (
    <div className="mb-6 md:mb-8">
      <div className="flex gap-4 items-baseline mb-2">
        {number && <span className="zil-section-number">{number}</span>}
        <h2 className="font-display text-lg md:text-xl uppercase tracking-wide leading-tight">
          {title}
        </h2>
      </div>
      {description && (
        <p className="text-sm md:text-base text-zil-soft leading-relaxed zil-prose">
          {description}
        </p>
      )}
    </div>
  );
}
