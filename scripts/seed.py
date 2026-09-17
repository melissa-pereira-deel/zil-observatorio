"""Popula o banco com o conjunto mínimo de dados reais para a plataforma fazer sentido.

Este NÃO é um seed de dados fictícios — num projeto cuja premissa é "todo dado é
público e auditável", dado inventado no banco é passivo, não conveniência.

O que ele faz é sincronizar da API da Câmara exatamente as votações que já
passaram por curadoria editorial em `data/direcoes/*.yml`, aplicar as direções
esperadas e recalcular os scores. O resultado é um banco pequeno, real e
rastreável até o YAML que o originou.

Uso (da raiz do repositório):

    python scripts/seed.py              # sync + aplicar direções + recalcular
    python scripts/seed.py --dry-run    # mostra o que faria, sem gravar
    python scripts/seed.py --skip-sync  # só reaplica direções (banco já populado)

Requer acesso de rede à API da Câmara, exceto com --skip-sync.
"""

import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _contar_direcoes() -> int:
    """Quantas votações estão curadas nos YAMLs — o insumo deste seed."""
    import yaml

    total = 0
    data_dir = REPO_ROOT / "data" / "direcoes"
    for arquivo in sorted(data_dir.glob("*.yml")):
        conteudo = yaml.safe_load(arquivo.read_text()) or {}
        total += len(conteudo.get("direcoes") or [])
    return total


def _rodar(descricao: str, script: str, args: list[str]) -> None:
    """Executa um script do pipeline, abortando o seed se ele falhar."""
    print(f"\n── {descricao} " + "─" * max(0, 60 - len(descricao)))
    resultado = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / script), *args],
        cwd=REPO_ROOT,
    )
    if resultado.returncode != 0:
        print(f"\n✗ {script} falhou (código {resultado.returncode}). Seed interrompido.")
        sys.exit(resultado.returncode)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--dry-run", action="store_true",
                        help="Mostra o que seria feito, sem gravar no banco")
    parser.add_argument("--skip-sync", action="store_true",
                        help="Pula a busca na API da Câmara (banco já populado)")
    args = parser.parse_args()

    curadas = _contar_direcoes()
    print(f"Seed do ZIL Observatório — {curadas} votações curadas em data/direcoes/")

    if curadas == 0:
        print("\nNenhuma votação curada. O seed não tem o que popular.")
        print("Adicione entradas em data/direcoes/[ano].yml antes de rodar.")
        return

    flags = ["--dry-run"] if args.dry_run else []

    if args.skip_sync:
        print("(--skip-sync: pulando a sincronização com a API da Câmara)")
    else:
        _rodar("Sincronizando votações curadas da Câmara", "sync_votacoes_zil.py", flags)

    _rodar("Aplicando direções esperadas e recalculando scores", "apply_direcoes.py", flags)

    print("\n✓ Seed concluído.")
    if args.dry_run:
        print("  (dry run — nada foi gravado)")
    else:
        print("  O score de cada parlamentar reflete apenas as votações curadas acima.")
        print("  Ampliar data/direcoes/ é o que dá base estatística ao ranking.")


if __name__ == "__main__":
    main()
