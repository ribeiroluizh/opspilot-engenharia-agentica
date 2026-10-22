# Atalhos da turma. Rode `make` (sem nada) para ver a lista.
# Em todos os comandos, o Python usado é o do Codespace.
PY ?= python

# Arquivos que cada aula completa (usados pelo "pegar o bonde").
ARQ_AULA1 = opspilot/tools.py opspilot/prompts.py opspilot/agente_react.py aulas/aula1
ARQ_AULA2 = opspilot/grafo.py aulas/aula2
ARQ_AULA3 = opspilot/deep_agent.py aulas/aula3
ARQ_AULA4 = opspilot/observabilidade.py opspilot/avaliacao.py aulas/aula4 .github/workflows/agentic-ci.yml

.PHONY: help setup check lacunas test test-live aula1 aula2 aula2-grafo aula3 aula4 avaliar comparar-buscas bonde gabarito-aula lint

help: ## Mostra esta ajuda
	@grep -E '^[a-zA-Z0-9_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

setup: ## Reinstala as dependências (o Codespace já faz isso sozinho)
	$(PY) -m pip install -r requirements.txt && $(PY) -m pip install -e .

check: ## Diagnóstico do ambiente (rode no início de cada aula)
	$(PY) scripts/check_env.py

lacunas: ## Lista lacunas abertas (filtre com AULA=2)
	@$(PY) scripts/lacunas.py $(AULA)

test: ## Testes offline (sem custo, sem chave). Filtre com AULA=2
	$(PY) -m pytest $(if $(AULA),tests/test_aula$(AULA)_*.py,)

test-live: ## Testes que chamam a OpenAI
	$(PY) -m pytest -m live

lint: ## Verifica estilo com ruff
	ruff check opspilot aulas tests scripts

aula1: ## Roda o primeiro agente ReAct
	$(PY) -m aulas.aula1.a1_02_primeiro_agente

aula2: ## Roda a FSM com persistência e aprovação humana
	$(PY) -m aulas.aula2.a2_01_rodar_grafo --thread inc-2041

aula2-grafo: ## Desenha o grafo da Aula 2 (sem chave)
	$(PY) -m aulas.aula2.a2_02_desenhar_grafo

aula3: ## Roda o Deep Agent no INC-2041
	$(PY) -m aulas.aula3.a3_01_orquestrador

aula4: ## Roda a FSM com tracing no Langfuse
	$(PY) -m aulas.aula4.a4_01_tracing

comparar-buscas: ## Palavras-chave x busca semântica (hit rate)
	$(PY) -m aulas.aula4.a4_03_comparar_buscas

avaliar: ## Avaliação completa + gate (LIMITE=0.75)
	$(PY) -m aulas.aula4.a4_02_avaliar --limite $(or $(LIMITE),0.75)

# De onde vem o gabarito. Primeiro tenta o branch `solucoes` do próprio fork (origin).
# Forks criados com "Copy the main branch only" não têm esse branch: aí o gabarito
# vem direto do repositório oficial do curso. O resultado fica numa referência local
# própria, que não mexe nos branches do aluno.
GABARITO_URL ?= https://github.com/sergiogaiotto/opspilot-engenharia-agentica.git
GABARITO_REF = refs/opspilot/solucoes
BUSCAR_GABARITO = git fetch --quiet origin +refs/heads/solucoes:$(GABARITO_REF) 2>/dev/null \
	|| { echo "ℹ️  Seu fork não tem o branch solucoes. Buscando o gabarito no repositório do curso..."; \
	     git fetch --quiet $(GABARITO_URL) +refs/heads/solucoes:$(GABARITO_REF); } \
	|| { echo "❌ Não consegui baixar o gabarito. Confira a internet do Codespace e tente de novo."; exit 1; }

bonde: ## Ficou para trás? Traz o gabarito das aulas ANTERIORES à AULA=N
	@test -n "$(AULA)" || (echo "Use: make bonde AULA=3" && exit 1)
	@$(BUSCAR_GABARITO)
	@for n in 1 2 3 4; do \
	  if [ $$n -lt $(AULA) ]; then \
	    case $$n in 1) arqs="$(ARQ_AULA1)";; 2) arqs="$(ARQ_AULA2)";; 3) arqs="$(ARQ_AULA3)";; 4) arqs="$(ARQ_AULA4)";; esac; \
	    echo "🚋 Trazendo gabarito da Aula $$n"; git checkout $(GABARITO_REF) -- $$arqs || exit 1; \
	  fi; \
	done
	@echo "✅ Pronto para a Aula $(AULA). Seu trabalho anterior está no histórico do git."

gabarito-aula: ## Mostra o diff entre seu código e o gabarito da AULA=N
	@test -n "$(AULA)" || (echo "Use: make gabarito-aula AULA=2" && exit 1)
	@$(BUSCAR_GABARITO)
	@case $(AULA) in 1) arqs="$(ARQ_AULA1)";; 2) arqs="$(ARQ_AULA2)";; 3) arqs="$(ARQ_AULA3)";; 4) arqs="$(ARQ_AULA4)";; esac; \
	git --no-pager diff HEAD $(GABARITO_REF) -- $$arqs
