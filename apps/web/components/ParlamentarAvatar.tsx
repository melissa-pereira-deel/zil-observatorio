"use client";

import { useState } from "react";

interface ParlamentarAvatarProps {
  nome: string;
  fotoUrl: string | null;
  size?: "sm" | "md" | "lg";
}

const SIZE_CLASSES = {
  sm: "w-10 h-10 text-xs",
  md: "w-12 h-12 text-sm",
  lg: "w-20 h-20 text-lg",
} as const;

function getInitials(nome: string): string {
  return nome
    .split(" ")
    .filter((w) => w.length > 0)
    .slice(0, 2)
    .map((w) => w[0])
    .join("")
    .toUpperCase();
}

export function ParlamentarAvatar({
  nome,
  fotoUrl,
  size = "md",
}: ParlamentarAvatarProps) {
  const [imgError, setImgError] = useState(false);
  const showImg = !!fotoUrl && !imgError;

  return (
    <div
      className={`${SIZE_CLASSES[size]} rounded-full bg-zil-card overflow-hidden shrink-0 flex items-center justify-center`}
    >
      {showImg ? (
        <img
          src={fotoUrl}
          alt={nome}
          className="w-full h-full object-cover"
          loading="lazy"
          onError={() => setImgError(true)}
        />
      ) : (
        <span className="font-display text-zil-soft select-none">
          {getInitials(nome)}
        </span>
      )}
    </div>
  );
}
