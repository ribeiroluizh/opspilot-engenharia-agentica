"""Testes OFFLINE da busca semântica (Aula 4): chunking, índice e comparação.

Usam um modelo de embeddings falso e determinístico, sem chave e sem custo.
"""

import pytest

from opspilot import busca_semantica as b

pytest.importorskip("numpy", reason="o InMemoryVectorStore usa numpy (rode make setup)")


def test_chunks_cortados_pelos_titulos_e_com_origem():
    chunks = b.carregar_chunks()
    runbooks = {c.metadata["runbook"] for c in chunks}
    assert runbooks == {
        "api-latencia-alta.md", "banco-conexoes-esgotadas.md", "certificado-expirando.md", "fila-mensagens-atrasada.md"
    }
    secoes = {c.metadata["secao"] for c in chunks if c.metadata["runbook"] == "banco-conexoes-esgotadas.md"}
    assert any(s.endswith("› Mitigação") for s in secoes), secoes
    assert all(b.contar_tokens(c.page_content) <= b.TAMANHO_CHUNK for c in chunks)


def test_secao_longa_vira_varios_chunks_com_sobreposicao():
    texto = " ".join(f"palavra{i}" for i in range(3000))
    partes = b._fatiar_por_tokens(texto, tamanho=100, sobreposicao=25)
    assert len(partes) > 1
    assert all(b.contar_tokens(p) <= 100 for p in partes)
    fim_da_primeira = partes[0].split()[-3:]
    assert any(palavra in partes[1] for palavra in fim_da_primeira)  # a sobreposição repete o final


def test_busca_devolve_top_k_com_runbook_de_origem():
    from langchain_core.embeddings import DeterministicFakeEmbedding

    indice = b.construir_indice(embeddings=DeterministicFakeEmbedding(size=64))
    resultados = b.buscar_semantico("o banco está recusando novas sessões", indice=indice)
    assert len(resultados) == b.TOP_K
    assert all(doc.metadata["runbook"].endswith(".md") for doc, _ in resultados)
    assert "similaridade" in b.formatar_resultados(resultados)


def test_dataset_de_buscas_aponta_para_runbooks_que_existem():
    from aulas.aula4.a4_03_comparar_buscas import carregar_perguntas
    from opspilot.config import DIR_RUNBOOKS

    perguntas = carregar_perguntas()
    assert len(perguntas) >= 10
    existentes = {p.name for p in DIR_RUNBOOKS.glob("*.md")}
    assert all(p["runbook_esperado"] in existentes for p in perguntas)


def test_pesquisador_tem_as_duas_buscas():
    try:
        from opspilot import deep_agent as d
    except NameError:
        pytest.skip("complete as lacunas da Aula 3 (ou rode make bonde AULA=4)")

    nomes = {f.name for f in d.PESQUISADOR_DE_RUNBOOKS["tools"]}
    assert nomes == {"buscar_runbook", "buscar_runbook_semantico"}
