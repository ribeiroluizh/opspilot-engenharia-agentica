# 🛰️ OpsPilot — Codebase de Referência

**Engenharia Agêntica: do Zero ao Deploy** · Skills & Go · Alura + FIAP
Formação hands-on de 12h (4 aulas) · Nivelamento, Arquitetura e Produção

O OpsPilot é um agente de **triagem de incidentes** para a loja fictícia *MercadoNimbus*.
Você vai construí-lo do zero, uma camada por aula, até ele estar observável, avaliado e com gate de CI.

```
Aula 1  ReAct (create_agent) ──▶ Aula 2  FSM (LangGraph) ──▶ Aula 3  Deep Agent (harness) ──▶ Aula 4  Langfuse + Evals + CI
```

---

## 🚀 Começando (5 minutos)

1. **Faça um fork** deste repositório (botão *Fork*, desmarque “Copy the main branch only” para trazer o branch `solucoes`; se esquecer, o `make bonde` busca o gabarito direto neste repositório).
2. Cadastre os secrets em **github.com → Settings → Codespaces → New secret**, liberando para o seu fork:
   - `OPENAI_API_KEY` (obrigatório)
   - `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_BASE_URL` (só na Aula 4)
3. No seu fork: **Code → Codespaces → Create codespace on main**. Aguarde o `post-create` terminar.
4. No terminal: `make check` → tudo ✅? Siga o **Guia do Aluno**.

> Rodando fora do Codespace? `cp .env.example .env`, preencha, e rode `make setup`.

## 🧭 Comandos do dia a dia

| Comando | O que faz |
|---|---|
| `make` | lista todos os atalhos |
| `make check` | diagnóstico do ambiente (rode no início de cada aula) |
| `make lacunas AULA=1` | mostra as lacunas que faltam preencher |
| `make test AULA=1` | testes offline da aula (sem custo) |
| `make aula1` … `make aula4` | roda o exercício principal de cada aula |
| `make gabarito-aula AULA=2` | compara seu código com o gabarito |
| `make bonde AULA=3` | ficou para trás? traz o gabarito das aulas anteriores |
| `make avaliar` | avaliação completa + gate de qualidade |

## 🧩 Como funcionam as lacunas

Nos arquivos do branch `main` você encontra blocos assim:

```python
# ┌─ LACUNA [A1-L5] Monte o agente: modelo + ferramentas + prompt
# │  Dica: create_agent recebe o modelo, a lista de ferramentas e o system_prompt...
# │  Copilot Chat: "Crie o agente com create_agent passando model=obter_llm(), ..."
# └─ Troque cada ___ abaixo. Gabarito: `make gabarito-aula AULA=1`
agente = create_agent(
    model=___,
    ...
```

Três níveis de ajuda, nesta ordem: **1) dica** → **2) prompt pronto para o Copilot Chat** → **3) gabarito**.
Erro `NameError: name '___' is not defined`? Significa que ainda há lacuna aberta — rode `make lacunas`.

## 🗂️ Estrutura

```
opspilot/                 ← o produto (cresce a cada aula)
  config.py               modelo, chaves, caminhos (fonte única de configuração)
  tools.py                Aula 1 · ferramentas (@tool)
  prompts.py              Aula 1 · prompt estruturado em seções
  agente_react.py         Aula 1 · create_agent (ReAct)
  grafo.py                Aula 2 · FSM em LangGraph (rotas, retry, interrupt, persistência)
  deep_agent.py           Aula 3 · harness: planejamento, filesystem, sub-agentes, memória
  observabilidade.py      Aula 4 · Langfuse (traces + scores)
  avaliacao.py            Aula 4 · regras + LLM-as-a-judge
aulas/aulaN/              ← scripts executáveis de cada aula (python -m aulas.aulaN.<arquivo>)
data/                     ← "a empresa": runbooks, métricas, logs, incidentes, dataset de avaliação
workspace/                ← disco do Deep Agent (notas, relatórios, memoria/AGENTS.md)
tests/                    ← testes offline por aula + testes live (pytest -m live)
.github/workflows/        ← Agentic CI/CD (testes + avaliação com gate)
.github/copilot-instructions.md ← ensina o Copilot a usar as APIs certas deste projeto
```

## 🌿 Branches

- `main` — versão com lacunas (onde você trabalha).
- `solucoes` — gabarito completo. Use com moderação.

> **CI no `main` com lacunas abertas falha de propósito**: os testes ficam verdes conforme você completa as aulas.

## 📚 Stack (versões conferidas em out/2026)

LangChain 1.4 · LangGraph 1.2 · deepagents 0.7 · Langfuse SDK 4 · OpenAI (`OPENAI_MODEL`, padrão `openai:gpt-5.4-mini`).

## ⚖️ Licença e créditos

Material didático do Skills & Go (Alura + FIAP). Exemplos inspirados em
[`langchain-ai/deepagents`](https://github.com/langchain-ai/deepagents) (MIT). Dados 100% fictícios.
