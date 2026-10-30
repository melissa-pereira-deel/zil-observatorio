/**
 * Peças de texto do sistema: chapéu + título de seção, citação em serifa e
 * foto com legenda em vidro.
 */

/** Chapéu em caixa alta (rótulo) acima do título. Espaço, não linha, separa seções. */
export function TituloSecao({
  chapeu,
  titulo,
  descricao,
  nivel = 2,
  tamanho = "titulo-2",
  className = "",
}: {
  chapeu?: string;
  titulo: React.ReactNode;
  descricao?: React.ReactNode;
  nivel?: 1 | 2 | 3;
  tamanho?: "display-l" | "display-m" | "titulo-1" | "titulo-2" | "titulo-3";
  className?: string;
}) {
  const Tag = `h${nivel}` as const;
  const TAM = {
    "display-l": "text-display-m md:text-display-l",
    "display-m": "text-titulo-1 md:text-display-m",
    "titulo-1": "text-titulo-2 md:text-titulo-1",
    "titulo-2": "text-titulo-3 md:text-titulo-2",
    "titulo-3": "text-titulo-3",
  }[tamanho];
  return (
    <div className={`grid gap-3 mb-8 md:mb-10 ${className}`}>
      {chapeu && <p className="text-rotulo uppercase text-zil-texto-2">{chapeu}</p>}
      <Tag className={TAM}>{titulo}</Tag>
      {descricao && <p className="text-texto-l text-zil-texto-2 max-w-[60ch]">{descricao}</p>}
    </div>
  );
}

/** Citação em destaque, com crédito. Uma por seção; nunca frase inventada. */
export function Citacao({
  children,
  autor,
  fonte,
  className = "",
}: {
  children: React.ReactNode;
  autor?: React.ReactNode;
  fonte?: React.ReactNode;
  className?: string;
}) {
  return (
    <figure className={`grid gap-4 m-0 ${className}`}>
      <blockquote className="m-0 text-citacao text-balance">{children}</blockquote>
      {(autor || fonte) && (
        <figcaption className="text-[15px] leading-5 font-semibold">
          {autor}
          {fonte && <small className="block font-normal text-zil-texto-2">{fonte}</small>}
        </figcaption>
      )}
    </figure>
  );
}

/** Foto com raio-xl e legenda em vidro (título e crédito). O alt descreve a cena. */
export function Foto({
  src,
  alt,
  titulo,
  credito,
  className = "",
  imgClassName = "",
}: {
  src: string;
  alt: string;
  titulo?: string;
  credito?: string;
  className?: string;
  imgClassName?: string;
}) {
  return (
    <figure className={`group relative m-0 overflow-hidden rounded-xl bg-zil-superficie-2 ${className}`}>
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={src}
        alt={alt}
        className={`block w-full h-full object-cover transition-transform duration-lenta ease-padrao group-hover:scale-[1.02] ${imgClassName}`}
      />
      {(titulo || credito) && (
        <figcaption className="zil-vidro absolute left-3 bottom-3 max-w-[calc(100%-24px)] grid gap-0.5 px-3.5 py-2.5 rounded-2xl text-[14px] leading-[18px] font-semibold text-zil-texto">
          {titulo}
          {credito && <small className="text-[12px] leading-4 font-medium text-zil-texto-2">{credito}</small>}
        </figcaption>
      )}
    </figure>
  );
}
