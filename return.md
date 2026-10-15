
✅ Resposta final:
## Causa raiz
O problema raiz é o **esgotamento do pool de conexões do `pagamentos-db`** após uma mudança de configuração no deploy de 2026-10-12 17:55, que reduziu o pool de **50 para 10**. Isso deixou o checkout sem conexões disponíveis e gerou `PoolTimeout`, resultando em 503s.

## Evidências
- `checkout-api`:
  - `latencia_p95_ms`: **4200 ms** vs baseline **380 ms**
  - `taxa_erro_pct`: **7.4%** vs baseline **0.3%**
  - CPU da API: **41%** (baixa, sugerindo dependência como gargalo)
- Logs do `checkout-api`:
  - `PoolTimeout: could not acquire connection from pool 'pagamentos' within 3000ms`
  - `POST /checkout 503 3012ms`
  - `db.acquire slow wait=1450ms`, `2210ms`, `2890ms`
- `pagamentos-db`:
  - `conexoes_ativas`: **10**
  - `conexoes_max_pool`: **10**
  - `baseline_conexoes_max_pool`: **50**
  - `espera_por_conexao_p95_ms`: **3100 ms**
  - CPU do banco: **23%** (baixa, compatível com fila/espera por pool)
- Logs do `pagamentos-db`:
  - `pgbouncer restart: pool_mode=transaction default_pool_size=10 (antes: 50) origem=DB_POOL_SIZE`
  - `DB_POOL_MAX ausente; usando default_pool_size como limite`
- Correlacionado com deploy/config:
  - `ultimo_deploy` do `pagamentos-db`: `config v2.14.0 em 2026-10-12 17:55 (refatoração de variáveis de ambiente do pool)`

## Sintomas vs. causa
**Sintomas:**
- Checkout lento
- 503 nas requisições
- p95 alto
- Erros de aquisição de conexão no `checkout-api`

**Causa raiz:**
- Redução da capacidade do pool do `pagamentos-db` de 50 para 10, causando contenção e timeouts de conexão.

## Ação recomendada
Seguindo o runbook:
1. **Reverter a configuração do pool** do `pagamentos-db` para o último valor estável.
2. **Reiniciar os pods consumidores em lotes** para liberar conexões presas.
3. Validar que `espera_por_conexao_p95_ms` volte para menos de **50 ms**.
4. Monitorar novamente `latencia_p95_ms`, `taxa_erro_pct` e `conexoes_ativas/max_pool`.

Se quiser, eu posso abrir o ticket de incidente agora com base nessa evidência.

## Severidade (SEV1/SEV2/SEV3)
**SEV1** — há impacto direto no checkout, com erros 503 e taxa de erro acima de 5%.

📊 Total de mensagens no estado: 13