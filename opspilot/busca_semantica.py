"""Aula 4 — Busca semântica nos runbooks (RAG sem banco vetorial).

A ``buscar_runbook`` da Aula 1 compara **palavras**. Esta ferramenta compara
**significados**: a pergunta e os trechos dos runbooks viram embeddings (listas
de números) e a busca devolve os trechos mais próximos.

As quatro etapas
----------------
1. **Carregar** os runbooks de ``data/runbooks/``, guardando o nome do arquivo.
2. **Dividir em chunks**: primeiro pelos títulos do Markdown (cada seção vira um
   chunk com sentido próprio); seções longas são subdivididas em pedaços de até
   ``TAMANHO_CHUNK`` tokens, com ``SOBREPOSICAO`` tokens repetidos entre um
   pedaço e o seguinte.
3. **Gerar os embeddings** com ``MODELO_EMBEDDING`` e guardar tudo num
   ``InMemoryVectorStore`` (na memória do programa, sem banco vetorial). O índice
   é montado uma vez por execução e reaproveitado nas consultas seguintes.
4. **Consultar**: a pergunta vira embedding, e a busca devolve os ``TOP_K``
   trechos mais parecidos (similaridade de cosseno), com o runbook de origem.

Testes offline: ``construir_indice(embeddings=...)`` aceita qualquer modelo de
embeddings, inclusive um falso (``DeterministicFakeEmbedding``), sem chave.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from functools import lru_cache

from langchain_core.documents import Document
from langchain_core.tools import tool

from opspilot.config import DIR_RUNBOOKS

TAMANHO_CHUNK = 512  # tokens
SOBREPOSICAO = 128  # tokens
TOP_K = 3
MODELO_EMBEDDING = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

_TITULO = re.compile(r"^(#{1,6})\s+(.*)$")


# --------------------------------------------------------------------------- #
# Contagem de tokens
# --------------------------------------------------------------------------- #


@lru_cache(maxsize=1)
def _codificador():
    """Codificador de tokens do tiktoken (instalado junto com o langchain-openai)."""
    try:
        import tiktoken

        return tiktoken.get_encoding("cl100k_base")
    except Exception:  # sem tiktoken: aproximação de 4 caracteres por token
        return None


def contar_tokens(texto: str) -> int:
    codificador = _codificador()
    return len(codificador.encode(texto)) if codificador else max(1, len(texto) // 4)


def _fatiar_por_tokens(texto: str, tamanho: int, sobreposicao: int) -> list[str]:
    """Divide um texto em pedaços de até ``tamanho`` tokens, repetindo ``sobreposicao`` tokens."""
    if contar_tokens(texto) <= tamanho:
        return [texto]
    passo = tamanho - sobreposicao
    codificador = _codificador()
    if codificador:
        tokens = codificador.encode(texto)
        janelas = [tokens[i : i + tamanho] for i in range(0, len(tokens), passo)]
        return [codificador.decode(janela) for janela in janelas if janela]
    caracteres, passo_c = tamanho * 4, passo * 4
    return [texto[i : i + caracteres] for i in range(0, len(texto), passo_c) if texto[i : i + caracteres]]


# --------------------------------------------------------------------------- #
# Etapas 1 e 2: carregar e dividir
# --------------------------------------------------------------------------- #


@dataclass
class Secao:
    titulo: str
    texto: str


def dividir_por_titulos(markdown: str) -> list[Secao]:
    """Corta o Markdown nos títulos. Cada seção leva o título do runbook e o da própria seção."""
    titulo_doc, secoes, atual, linhas = "", [], "", []
    for linha in markdown.splitlines():
        achou = _TITULO.match(linha)
        if achou:
            if linhas and "".join(linhas).strip():
                secoes.append(Secao(atual, "\n".join(linhas).strip()))
            nivel, nome = len(achou.group(1)), achou.group(2).strip()
            if nivel == 1:
                titulo_doc = nome
                atual = nome
            else:
                atual = f"{titulo_doc} › {nome}" if titulo_doc else nome
            linhas = [linha]
        else:
            linhas.append(linha)
    if linhas and "".join(linhas).strip():
        secoes.append(Secao(atual, "\n".join(linhas).strip()))
    return secoes


def carregar_chunks(
    diretorio=DIR_RUNBOOKS, tamanho: int = TAMANHO_CHUNK, sobreposicao: int = SOBREPOSICAO
) -> list[Document]:
    """Lê os runbooks e devolve os chunks, cada um com ``runbook`` e ``secao`` nos metadados."""
    chunks: list[Document] = []
    for arquivo in sorted(diretorio.glob("*.md")):
        for secao in dividir_por_titulos(arquivo.read_text(encoding="utf-8")):
            for parte, texto in enumerate(_fatiar_por_tokens(secao.texto, tamanho, sobreposicao)):
                metadados = {"runbook": arquivo.name, "secao": secao.titulo, "parte": parte}
                chunks.append(Document(page_content=texto, metadata=metadados))
    return chunks


# --------------------------------------------------------------------------- #
# Etapas 3 e 4: embeddings e consulta
# --------------------------------------------------------------------------- #


def construir_indice(embeddings=None, diretorio=DIR_RUNBOOKS):
    """Gera os embeddings de todos os chunks e guarda num ``InMemoryVectorStore``."""
    from langchain_core.vectorstores import InMemoryVectorStore

    if embeddings is None:
        from langchain_openai import OpenAIEmbeddings

        embeddings = OpenAIEmbeddings(model=MODELO_EMBEDDING)
    indice = InMemoryVectorStore(embedding=embeddings)
    indice.add_documents(carregar_chunks(diretorio))
    return indice


@lru_cache(maxsize=1)
def _indice_padrao():
    """Índice da execução atual: os embeddings são calculados só na primeira consulta."""
    return construir_indice()


def buscar_semantico(consulta: str, k: int = TOP_K, indice=None) -> list[tuple[Document, float]]:
    """Devolve os ``k`` chunks mais parecidos com a consulta, com a similaridade de cosseno."""
    indice = indice or _indice_padrao()
    return indice.similarity_search_with_score(consulta, k=k)


def formatar_resultados(resultados: list[tuple[Document, float]]) -> str:
    if not resultados:
        return "Nenhum trecho de runbook encontrado."
    return "\n\n---\n\n".join(
        f"[{doc.metadata['runbook']} · {doc.metadata['secao']} · similaridade {nota:.2f}]\n{doc.page_content}"
        for doc, nota in resultados
    )


@tool
def buscar_runbook_semantico(consulta: str) -> str:
    """Busca nos runbooks internos os trechos com SIGNIFICADO mais próximo da pergunta.

    Use quando a pergunta descreve o problema com outras palavras (ex.: "o banco
    recusa novas sessões", "o cadeado do site vai vencer"). Devolve os 3 trechos
    mais parecidos, cada um com o nome do runbook e da seção de origem.

    Args:
        consulta: A pergunta ou o sintoma descrito em linguagem natural.
    """
    try:
        return formatar_resultados(buscar_semantico(consulta))
    except ImportError as erro:
        return f"ERRO: dependência ausente para a busca semântica ({erro}). Rode `make setup` no terminal."
    except Exception as erro:
        return f"ERRO na busca semântica: {erro}. Use buscar_runbook (palavras-chave) como alternativa."
