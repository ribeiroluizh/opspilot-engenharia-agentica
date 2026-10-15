"""Testes OFFLINE das ferramentas (não chamam o LLM; rodam no CI sem chave).

Ferramentas são código comum: devem ter testes comuns. Repare que testamos
inclusive o caminho de ERRO — é ele que permite a autocorreção do agente.
"""

import json

from opspilot import tools


def test_consultar_metricas_servico_valido():
    saida = json.loads(tools.consultar_metricas.invoke({"servico": "pagamentos-db"}))
    assert saida["conexoes_max_pool"] == 10
    assert saida["baseline_conexoes_max_pool"] == 50


def test_consultar_metricas_erro_vira_observacao():
    saida = tools.consultar_metricas.invoke({"servico": "checkout"})
    assert saida.startswith("ERRO")
    assert "checkout-api" in saida  # lista os nomes válidos para o agente se corrigir


def test_ler_logs_com_filtro():
    saida = tools.ler_logs.invoke({"servico": "pagamentos-db", "filtro": "pool_size"})
    assert "default_pool_size=10" in saida


def test_ler_logs_limita_linhas():
    saida = tools.ler_logs.invoke({"servico": "checkout-api", "max_linhas": 3})
    assert len(saida.splitlines()) == 3


def test_listar_deploys_filtra_e_ordena_logs(monkeypatch, tmp_path):
    from datetime import UTC, datetime, timedelta

    agora = datetime.now(UTC)
    monkeypatch.setattr(tools, "DIR_LOGS", tmp_path)
    (tmp_path / "servico-a.log").write_text(
        f"{(agora - timedelta(hours=2)).isoformat()} INFO deploy mais antigo\n"
        f"{(agora - timedelta(hours=8)).isoformat()} INFO deploy antigo\n",
        encoding="utf-8",
    )
    (tmp_path / "servico-b.log").write_text(
        f"{(agora - timedelta(hours=1)).isoformat()} INFO deploy mais recente\n",
        encoding="utf-8",
    )

    saida = tools.listar_deploys.invoke({"horas": 6})

    assert saida.splitlines() == [
        f"{(agora - timedelta(hours=2)).isoformat()} INFO deploy mais antigo",
        f"{(agora - timedelta(hours=1)).isoformat()} INFO deploy mais recente",
    ]
    assert tools.listar_deploys in tools.TODAS_FERRAMENTAS


def test_buscar_runbook_encontra_pool():
    saida = tools.buscar_runbook.invoke({"consulta": "pool de conexões esgotado"})
    assert "banco-conexoes-esgotadas.md" in saida


def test_abrir_ticket_grava_arquivo(tmp_path, monkeypatch):
    monkeypatch.setattr(tools, "DIR_TICKETS", tmp_path)
    saida = tools.abrir_ticket.invoke(
        {"titulo": "Teste", "servico": "pagamentos-db", "severidade": "SEV2", "resumo": "teste"}
    )
    assert "aberto" in saida
    assert len(list(tmp_path.glob("OPS-*.json"))) == 1


def test_schema_da_ferramenta_tem_descricao():
    """O LLM só usa bem o que entende: docstring e parâmetros precisam chegar no schema."""
    schema = tools.consultar_metricas.args
    assert "servico" in schema
    assert "métricas" in tools.consultar_metricas.description.lower()
