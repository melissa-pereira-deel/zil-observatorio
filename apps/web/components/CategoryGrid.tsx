import Link from "next/link";

const CATEGORIES = [
  { code: "ZIL-FER", name: "Fertilizantes", emoji: "\uD83C\uDF31" },
  { code: "ZIL-MIN", name: "Minerais", emoji: "\u26CF\uFE0F" },
  { code: "ZIL-SEM", name: "Semicondutores", emoji: "\uD83D\uDD2C" },
  { code: "ZIL-ENE", name: "Energia", emoji: "\u26A1" },
  { code: "ZIL-DIG", name: "Digital", emoji: "\uD83D\uDCE1" },
  { code: "ZIL-DEF", name: "Defesa", emoji: "\uD83D\uDEE1\uFE0F" },
  { code: "ZIL-EDU", name: "Capital Humano", emoji: "\uD83C\uDF93" },
  { code: "ZIL-AGR", name: "Agro-Indústria", emoji: "\uD83C\uDFED" },
  { code: "ZIL-COM", name: "Comércio", emoji: "\uD83C\uDF10" },
];

export function CategoryGrid() {
  return (
    <div className="grid grid-cols-3 gap-2 md:gap-3">
      {CATEGORIES.map((cat) => (
        <Link
          key={cat.code}
          href={`/proposicoes?categoria=${cat.code}`}
          className="group flex flex-col items-center gap-2 p-4 md:p-5 border border-zil-divider hover:border-zil-green hover:bg-zil-green-light/30 transition-all duration-200 text-center"
        >
          <span className="text-xl md:text-2xl" role="img" aria-label={cat.name}>
            {cat.emoji}
          </span>
          <span className="text-xs md:text-sm font-medium text-zil-soft group-hover:text-zil-green transition-colors">
            {cat.name}
          </span>
          <span className="font-mono text-2xs text-zil-muted tracking-wider">
            {cat.code}
          </span>
        </Link>
      ))}
    </div>
  );
}
