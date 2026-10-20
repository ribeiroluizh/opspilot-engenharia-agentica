"""Testes OFFLINE do harness da Aula 3 (estrutura, sem chamar o LLM)."""

from opspilot import deep_agent as d


def test_subagentes_tem_campos_obrigatorios():
    for spec in (d.ANALISTA_DE_LOGS, d.PESQUISADOR_DE_RUNBOOKS):
        assert spec["name"] and len(spec["description"]) > 30, "description é o que o orquestrador lê para delegar"
        assert spec["tools"], "sub-agente sem ferramentas não consegue pesquisar"


def test_analista_so_tem_ferramentas_de_leitura():
    nomes = {f.name for f in d.ANALISTA_DE_LOGS["tools"]}
    assert nomes == {"ler_logs", "consultar_metricas"}


def test_grafo_da_aula2_encapsulado_como_subagente():
    spec = d.criar_subagente_triagem()
    assert spec["name"] == "triagem-fsm"
    nos = set(spec["runnable"].get_graph().nodes)
    assert "aprovar_ticket" not in nos  # dentro do harness, quem aprova é o orquestrador


def test_backend_roteia_base_e_memoria():
    backend = d.criar_backend()
    incidente = backend.read("/base/incidentes/INC-2041.md")
    assert incidente.error is None, incidente.error
    memoria = backend.read("/memoria/AGENTS.md")
    assert memoria.error is None, memoria.error


def test_base_e_somente_leitura():
    regra = d.PERMISSOES[0]
    assert regra.mode == "deny" and "write" in regra.operations and "/base/**" in regra.paths


def test_deep_agent_compila_sem_rede(monkeypatch):
    """Com uma chave falsa o modelo é instanciado, mas nenhuma chamada é feita."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-teste-offline-0000000000000000")
    agente = d.criar_deep_agent()
    assert hasattr(agente, "invoke") and hasattr(agente, "stream")
