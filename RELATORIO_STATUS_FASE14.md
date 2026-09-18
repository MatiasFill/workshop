# Oficina AI — Relatório de status (17/09/2026)

Sistema de gestão para oficina mecânica: backend Python/FastAPI + PostgreSQL/Redis,
frontend React/Vite/TypeScript, módulo de IA (gateway multi-provider, RAG, OCR).
Este relatório documenta tudo que já foi entregue e tudo que falta até a
conclusão, para retomar o trabalho a qualquer momento sem perder contexto.

**Arquivo do código correspondente a este relatório:** `oficina-ai-fase14-kanban.zip`

---

## 1. Concluído (FASES 1 a 12)

| Fase | Entrega |
|---|---|
| 1 | Fundação multiempresa: `Company`/`Branch`/`User`/`Role`/`Permission` (RBAC real), sessão por cookie+Redis, RLS no Postgres, senha com PBKDF2 |
| 2 | Clientes e veículos: cadastro, normalização de placa/documento, exclusão lógica |
| 3 | Agenda: `Appointment`, checagem de conflito de horário por mecânico, cancelamento |
| 4/5 | Estoque, Ordens de Serviço, comprovante por e-mail/WhatsApp (SMTP/HTTP, best-effort), alerta de revisão próxima do vencimento, dashboard com gráficos |
| 6 | Financeiro/Caixa: contas a pagar/receber, abertura/fechamento de caixa, reforço/sangria; fechar OS gera `FinanceEntry` automaticamente |
| 7 | Compras/Fornecedores: pedido de compra, recebimento dá entrada automática no estoque e gera `FinanceEntry` a pagar |
| 8 | Audit log: trilha somente-inserção das ações sensíveis (login, OS, financeiro, caixa, estoque, compras) |
| 9 | LGPD: exportação de dados do cliente e anonimização (art. 15/18) |
| 10 | Retenção de dados: purga de notificações antigas, anonimização em massa de clientes inativos sem pendência (art. 6º VII) |
| 11 | Fila de notificações: retry com backoff exponencial, idempotência por `idempotency_key` |
| 12 | Barramento de eventos em processo (`app/core/events.py`), desacoplando ações de reações (ex.: fechar OS → disparar comprovante) |

Todas as fases têm migration própria com Row-Level Security por `company_id`,
permissão dedicada no catálogo RBAC quando aplicável, e testes (`backend/tests/`).

Também existe, à parte do fluxo de fases (feito localmente via Claude Code,
fora deste ambiente de chat):
- Dockerfiles + `docker-compose.yml` para backend/frontend/Postgres/Redis
- Manifests Kubernetes “cruos” em `k8s/` e um Helm chart em `helm/oficina-ai/`
- Correção de 2 warnings de depreciação (14× `datetime.utcnow()` → `utcnow_naive()`; 11× `class Config` do Pydantic v1 → `model_config = ConfigDict(...)`)

---

## 2. Concluída — FASE 13: checklist de inspeção veicular

Item pendente do P1 (orçamento/OS/checklist) desde a especificação original. **Fechada por completo.**

- [x] Modelo `WorkOrderChecklistItem` (status `NOT_CHECKED`/`OK`/`ATTENTION` + observação livre, quem checou e quando)
- [x] Migration `0011` com RLS (mesmo padrão das anteriores)
- [x] Rotas: `POST /work-orders/{id}/checklist`, `PATCH /work-orders/{id}/checklist/{item_id}`, `DELETE /work-orders/{id}/checklist/{item_id}` — reaproveitam a permissão `work_orders.update` já existente, sem precisar criar permissão nova
- [x] `checklist_items` incluído na resposta da OS (`WorkOrderResponse`)
- [x] Tela no frontend: botão "Checklist" em cada linha da tabela de OS, abre modal com status/observação por item, vira somente-leitura quando a OS está `DONE`/`CANCELLED`
- [x] Testes automatizados (`backend/tests/test_checklist.py`, 8 casos: add/list, update status+observação, remove, 404, bloqueio em OS encerrada, RECEPTION sem permissão, isolamento por empresa)
- [x] `README.md`/`docs/ROADMAP.md` atualizados (seção "FASE 13" documentada, checklist marcado como concluído, lista "Próximas fases" do README corrigida — estava desatualizada desde a FASE 3)

Validação feita até agora (sem Docker/Postgres/Redis disponíveis neste ambiente
de chat, só checagem estática): `py_compile` em todo o backend e `tsc --noEmit`
em todo o frontend, sem erro. **Falta rodar a suíte real** (`pytest`) com
Postgres/Redis de verdade, que este ambiente de chat não tem.

---

## 2.1. Concluída — FASE 14: kanban com cards arrastáveis

Sem tabela nova, sem migration, sem rota nova no backend — reaproveita os `PATCH` que já existiam.

- [x] Ordens de serviço: quadro kanban por status (Aberta → Em andamento → Aguardando aprovação → Aprovada → Concluída → Cancelada), drag nativo do HTML5 (sem lib nova — sem acesso à internet para `npm install` neste ambiente)
- [x] Agenda: mesmo padrão, colunas por status do agendamento (o backend reavalia conflito de horário/mecânico automaticamente ao mudar de coluna)
- [x] Card de item já encerrado não é arrastável; coluna sob o cursor é destacada durante o arraste
- [x] `README.md`/`docs/ROADMAP.md` atualizados com a seção "FASE 14"

Validado com `tsc --noEmit` no frontend inteiro, sem erro.

---

## 2.2. Melhorias locais de demonstração e interface

- [x] Carga idempotente de dados fictícios para clientes, veículos, agenda, ordens de serviço, estoque, fornecedor e financeiro em `backend/app/db/demo_data.py`
- [x] Dashboard com lucro fictício do mês, calculado a partir de uma OS concluída
- [x] Busca rápida de clientes pelo cabeçalho, com modal, consulta por nome/telefone/documento e navegação para Clientes
- [x] Modal de busca mantido no layout original, com redução apenas da altura da lista de resultados para evitar excesso de rolagem
- [x] Oficina Copilot movido para o botão "Consultar IA" ao lado da lupa, abrindo somente quando solicitado
- [x] Dashboard com cards e bordas coloridas consistentes
- [x] Agenda organizada em grade fixa de seis cards, com três status por linha

Validação local:

- `frontend`: `npm run build` concluído com sucesso
- API de saúde respondeu em `http://127.0.0.1:8000/api/health`
- Login de demonstração validado com `demo@oficina.local` / `demo123`
- Busca rápida testada com o cliente fictício "Ana Souza"
- Dashboard retornou `profit_this_month: 250.0`

Os arquivos foram mantidos no workspace local e preparados para registro no Git. Nenhum
push foi realizado.

## 3. O que falta até a conclusão do projeto

### P4 — Governança (ainda não iniciado)
- Monitoramento (health checks estruturados, métricas, alertas)
- Backup/restore do Postgres

### Tarefas hoje manuais, que pedem um agendador real
- `check_upcoming_revisions` (alerta de revisão)
- `POST /retention/purge-notifications` e `POST /retention/anonymize-inactive`
- `POST /notifications/process-queue`
- Precisam de um worker/cron (ex.: APScheduler ou um serviço separado) para rodar sozinhas

### P5 — IA avançada (não iniciado)
- Embeddings com pgvector, reranker, citações por página, memória semântica, avaliação de respostas, controle de custo por tenant

### Fora do escopo deste ambiente de chat (feito localmente via Claude Code, exige Docker/rede/kubectl reais)
- Deploy no Kind: travou no `kubeadm init` (erro de comunicação com `https://172.20.0.2:6443`), causa ainda não diagnosticada — ver `PROXIMO_PASSO_KIND.md` no projeto
- Envio automatizado do relatório em PDF por WhatsApp Business/Cloud API — falta número verificado e token de autenticação; ver `PROXIMO_PASSO_WHATSAPP.md`

---

## 4. Como retomar

O ambiente de chat não mantém arquivos entre conversas. Para continuar:
1. Reenviar o zip mais recente (`oficina-ai-fase14-kanban.zip` ou o que vier depois dele)
2. Indicar o próximo passo (ex.: "continue o frontend do checklist") ou pedir para eu escolher a melhor opção
3. O código e o relatório desta etapa estão no workspace e foram registrados no commit
   correspondente desta versão.
