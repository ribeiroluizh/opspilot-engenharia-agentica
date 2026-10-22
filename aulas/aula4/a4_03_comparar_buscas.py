"""Aula 4 — Palavras-chave x busca semântica: qual encontra o runbook certo?

Para cada pergunta de ``data/avaliacao/buscas.jsonl`` (com o runbook esperado),
roda as duas buscas e confere se o runbook certo apareceu entre os resultados.
A proporção de acertos é o **hit rate**: @3 na busca semântica (3 trechos) e
@2 na busca por palavras-chave, que devolve no máximo 2 runbooks.

Uso:
    make comparar-buscas
    python -m aulas.aula4.a4_03_comparar_buscas
    python -m aulas.aula4.a4_03_comparar_buscas --so-palavras   # sem chave e sem custo
"""

from __future__ import annotations

import argparse
import json
import re

from opspilot.busca_semantica import TOP_K, buscar_semantico
from opspilot.config import DIR_DADOS, tem_chave_openai
from opspilot.tools import buscar_runbook

ARQ_BUSCAS = DIR_DADOS / "avaliacao" / "buscas.jsonl"


def carregar_perguntas(caminho=ARQ_BUSCAS) -> list[dict]:
    return [json.loads(linha) for linha in caminho.read_text(encoding="utf-8").splitlines() if linha.strip()]


def runbooks_por_palavras(pergunta: str) -> list[str]:
    """Nomes dos runbooks devolvidos pela busca por palavras-chave (Aula 1)."""
    return re.findall(r"^\[([^\]]+\.md)\]", buscar_runbook.invoke({"consulta": pergunta}), re.M)


def runbooks_semanticos(pergunta: str, k: int = TOP_K) -> list[str]:
    """Nomes dos runbooks dos ``k`` trechos mais parecidos (sem repetir)."""
    nomes: list[str] = []
    for doc, _ in buscar_semantico(pergunta, k=k):
        if doc.metadata["runbook"] not in nomes:
            nomes.append(doc.metadata["runbook"])
    return nomes


def hit_rate(acertos: list[bool]) -> float:
    return sum(acertos) / len(acertos) if acertos else 0.0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--so-palavras", action="store_true", help="Roda só a busca por palavras-chave")
    args = parser.parse_args()

    usar_semantica = not args.so_palavras
    if usar_semantica and not tem_chave_openai():
        print("⚠️  Sem OPENAI_API_KEY: rodando só a busca por palavras-chave.\n")
        usar_semantica = False

    acertos_p, acertos_s = [], []
    for item in carregar_perguntas():
        esperado = item["runbook_esperado"]
        nomes_p = runbooks_por_palavras(item["pergunta"])
        acertos_p.append(esperado in nomes_p)
        linha = f"{'✅' if acertos_p[-1] else '❌'} palavras"
        if usar_semantica:
            nomes_s = runbooks_semanticos(item["pergunta"])
            acertos_s.append(esperado in nomes_s)
            linha += f"  {'✅' if acertos_s[-1] else '❌'} semântica"
        print(f"{item['id']}  {linha}  ·  {item['pergunta']}  →  esperado: {esperado}")

    print(f"\n📊 Hit rate  palavras-chave (@2): {hit_rate(acertos_p):.0%}", end="")
    print(f"  ·  semântica (@{TOP_K}): {hit_rate(acertos_s):.0%}" if usar_semantica else "")


if __name__ == "__main__":
    main()
