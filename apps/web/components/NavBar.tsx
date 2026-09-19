"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { rankingPublico } from "@/lib/flags";

const NAV_LINKS = [
  // O ranking só aparece quando a curadoria o sustenta (ver lib/flags.ts)
  ...(rankingPublico ? [{ href: "/ranking", label: "Ranking" }] : []),
  { href: "/proposicoes", label: "Proposições" },
  { href: "/", label: "Manifesto" },
  { href: "/metodologia", label: "Metodologia" },
];

export function NavBar() {
  const pathname = usePathname();
  const [menuOpen, setMenuOpen] = useState(false);

  const isActive = (href: string) => {
    if (href === "/") return pathname === "/";
    return pathname.startsWith(href);
  };

  return (
    <nav className="border-b border-zil-divider bg-zil-bg sticky top-0 z-50">
      <div className="max-w-5xl mx-auto px-5 md:px-8 py-4 flex items-center justify-between">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-3">
          <span className="font-display text-2xl tracking-wider">ZIL</span>
          <div className="flex gap-0.5">
            <div className="w-5 h-1 bg-zil-gold skew-x-[-12deg]" />
            <div className="w-2 h-1 bg-zil-green skew-x-[-12deg]" />
          </div>
        </Link>

        {/* Desktop links */}
        <div className="hidden md:flex items-center gap-6 text-sm font-medium">
          {NAV_LINKS.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={`transition-colors ${
                isActive(link.href)
                  ? "text-zil-green"
                  : "text-zil-soft hover:text-zil-green"
              }`}
            >
              {link.label}
            </Link>
          ))}
        </div>

        {/* Mobile hamburger */}
        <button
          onClick={() => setMenuOpen(!menuOpen)}
          className="md:hidden flex flex-col gap-1.5 p-2 -mr-2"
          aria-label={menuOpen ? "Fechar menu" : "Abrir menu"}
        >
          <span
            className={`w-5 h-0.5 bg-zil-fg transition-all duration-200 ${
              menuOpen ? "rotate-45 translate-y-[4px]" : ""
            }`}
          />
          <span
            className={`w-5 h-0.5 bg-zil-fg transition-all duration-200 ${
              menuOpen ? "-rotate-45 -translate-y-[4px]" : ""
            }`}
          />
        </button>
      </div>

      {/* Mobile menu */}
      {menuOpen && (
        <div className="md:hidden border-t border-zil-divider bg-zil-bg animate-fade-in">
          {NAV_LINKS.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              onClick={() => setMenuOpen(false)}
              className={`block px-5 py-3 text-sm font-medium border-b border-zil-divider transition-colors ${
                isActive(link.href)
                  ? "text-zil-green bg-zil-green-light/30"
                  : "text-zil-soft hover:bg-zil-card"
              }`}
            >
              {link.label}
            </Link>
          ))}
        </div>
      )}
    </nav>
  );
}
