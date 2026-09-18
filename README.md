# Oficina AI — Gestão de Oficina + RAG/OCR + LLM Gateway

Base de produção para refazer o projeto da especificação `especificacao-oficina-claude-code.md`,
com foco em Python, RAG, OCR, múltiplas APIs de LLM, modo memória para testes e frontend
responsivo em Tailwind.

> Este pacote é uma fundação executável, não uma implementação completa de todos os 104 itens
> da especificação. Os módulos críticos foram estruturados para crescer sem virar um monólito.

## Stack

- Backend: Python 3.12 + FastAPI + SQLAlchemy + Alembic + Pydantic
- Banco: PostgreSQL
- Cache/fila: Redis
- RAG: armazenamento de documentos/chunks + busca lexical local; adaptador de embeddings opcional
- OCR: PyMuPDF + pytesseract opcional
- LLM Gateway: OpenAI, Anthropic, Gemini e Ollama por adapters
- Memória: SQLite local para respostas de teste, com TTL e hash da pergunta/contexto
- Frontend: React + Vite + TypeScript + Tailwind CSS
- Validação: Pydantic + Zod
- Docker Compose para desenvolvimento

## Começar no VS Code

### 1. Requisitos

- Docker Desktop
- Python 3.12+
- Node 20+
- VS Code

### 2. Configuração

```bash
cp .env.example .env
docker compose up --build -d db redis backend frontend
```

> O `backend` e o `frontend` já vêm definidos em `docker-compose.yml`. Dentro do container, o backend usa `db` e `redis` como hosts do Docker, enquanto o frontend aponta para `http://localhost:8000/api`.

Backend (execução local fora do contêiner):

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Abra `http://localhost:5173`.

## Hardening dos endpoints de IA/RAG

Independente da FASE 1, estes controles já valem para `/api/ai/ask`, `/api/ai/memory`,
`/api/rag/ingest` e `/api/rag/documents` (além de RBAC + autenticação, ver seção FASE 1 acima):
- Rate limiting em memória por IP em `/api/ai/ask` e `/api/rag/ingest` (`RATE_LIMIT_*` no `.env`).
- Validação de extensão de arquivo em `/api/rag/ingest` (`RAG_ALLOWED_EXTENSIONS`).
- Paginação (`limit`/`offset`) em `GET /api/rag/documents`.
- `/docs`, `/redoc` e `/openapi.json` desativados automaticamente quando `APP_ENV=production`.

## FASE 1 — Autenticação real, RBAC e multiempresa

A partir daqui, a medida-ponte da chave de API interna foi **removida** e substituída por:

- **Autenticação por sessão** (cookie httpOnly + Redis) — não é JWT, escolhido de propósito por
  permitir revogação instantânea (ex.: funcionário desligado) sem precisar de blocklist.
- **RBAC por permissão**, com os papéis da especificação (`ADMIN`, `MANAGER`, `RECEPTION`,
  `MECHANIC`, `FINANCE`, `STOCK_MANAGER`) e permissões granulares (`app/core/rbac_catalog.py`).
- **Isolamento multiempresa em duas camadas**: filtro por `company_id` em todo service/query
  (camada de aplicação) **e** Row-Level Security no PostgreSQL (`migrations/versions/0002_*`) como
  defesa em profundidade — um bug de autorização no código não basta sozinho para vazar dados
  entre empresas quando rodando em Postgres. Em SQLite (modo dev sem Postgres) só a camada de
  aplicação vale, porque SQLite não suporta RLS.

### Rodar as migrations

```bash
cd backend
alembic upgrade head
```

### Popular papéis/permissões e (opcional) criar a primeira empresa + admin

Defina no `.env`:

```env
SEED_COMPANY_NAME=Oficina Exemplo
SEED_ADMIN_EMAIL=admin@exemplo.com
SEED_ADMIN_PASSWORD=troque-esta-senha
```

Depois rode:

```bash
python -m app.db.seed
```

É idempotente: pode rodar de novo sem duplicar nada. Sem essas três variáveis, ele só garante que
os papéis/permissões existem (não cria empresa/admin).

### Login

```bash
curl -i -c cookies.txt -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@exemplo.com","password":"troque-esta-senha"}'
```

O backend responde com um cookie `session_id` (httpOnly). Toda chamada seguinte deve enviar esse
cookie — no `curl`, use `-b cookies.txt`; no frontend, `fetch(..., {credentials: 'include'})` (já
configurado em `frontend/src/lib/api.ts`).

### Nota de design: e-mail é único globalmente, não só por empresa

Um mesmo e-mail não pode existir em duas empresas diferentes neste scaffold — o login busca o
usuário só pelo e-mail (`/api/auth/login` ainda não sabe a empresa antes de autenticar, é
exatamente isso que ele resolve). Isso é diferente do modelo "workspace" de algumas SaaS (onde o
mesmo e-mail pode ter contas em várias organizações). Se isso virar um requisito real, a mudança é:
adicionar um passo de seleção de empresa antes do login (por subdomínio ou por um campo extra).

### Limitação conhecida: permissões ficam "congeladas" até o próximo login

As permissões do usuário são resolvidas uma vez no login e guardadas na sessão do Redis. Se você
mudar o papel de alguém no meio do dia, isso só passa a valer no próximo login dessa pessoa. Para
FASE 1 isso é aceitável; se virar problema, o próximo passo é invalidar sessões ativas quando o
papel do usuário mudar.

## FASE 2 — Clientes e veículos

Endpoints protegidos por sessão + RBAC (permissões `customers.read/create/update/delete`,
ver `app/core/rbac_catalog.py`), com `company_id` sempre resolvido pela sessão — nunca pelo corpo
da requisição — e as mesmas duas camadas de isolamento multiempresa da FASE 1 (filtro em código +
RLS no Postgres via `migrations/versions/0003_*`).

- `GET /api/customers` — lista com busca (`q`) por nome/documento/telefone/e-mail e paginação.
- `POST /api/customers` — cria cliente, opcionalmente já com veículos.
- `GET /api/customers/{id}` / `PATCH /api/customers/{id}` / `DELETE /api/customers/{id}` (soft delete).
- `POST /api/customers/{id}/vehicles`, `PATCH .../vehicles/{id}`, `DELETE .../vehicles/{id}` (soft delete).

Regras de negócio:
- CPF/CNPJ é opcional, mas quando informado precisa ser único por empresa (índice único **parcial**
  — não bloqueia dois clientes sem documento na mesma empresa).
- Placa é obrigatória e única por empresa; é normalizada (maiúsculas, sem hífen/espaço) antes de
  gravar e de comparar.
- Exclusão é sempre lógica (`is_active=False`), tanto em cliente quanto em veículo, para não quebrar
  o histórico de ordens de serviço que vierem a referenciá-los nas próximas fases.

Tela correspondente no frontend: aba "Clientes" (listagem + busca + cadastro rápido com um veículo).

## FASE 3 — Agenda

Endpoints protegidos por sessão + RBAC (`appointments.read/create/update/cancel`, adicionadas ao
catálogo — **é preciso rodar `python -m app.db.seed` de novo** para essas permissões passarem a
existir no banco e serem associadas aos papéis).

- `GET /api/appointments` — lista com filtro por período (`date_from`/`date_to`), mecânico, cliente
  e status.
- `POST /api/appointments` — cria agendamento; valida que o veículo (se informado) pertence ao
  cliente informado, e que não há conflito de horário para o mesmo mecânico.
- `GET /api/appointments/{id}` / `PATCH /api/appointments/{id}` — consulta e edição (reavalia
  conflito só quando horário, duração ou mecânico mudam).
- `POST /api/appointments/{id}/cancel` — cancelamento (não é soft delete por flag `is_active`,
  é uma transição de status para `CANCELLED`, para manter o histórico de estados do agendamento).

Regras de negócio:
- Conflito de horário é checado **só quando há mecânico atribuído** (`mechanic_id`) — a versão
  atual não modela capacidade por baia/box, isso fica para uma fase futura de estoque/operação.
- Um agendamento `CANCELLED` ou `NO_SHOW` libera o horário automaticamente (não entra na checagem
  de conflito).
- Cada leitura de agendamento já vem enriquecida com `customer_name`/`vehicle_plate`, montados
  explicitamente nas rotas (sem depender de serialização "mágica" de atributos que não existem no
  modelo).

Tela correspondente no frontend: aba "Agenda" (lista cronológica + busca de cliente e veículo já
cadastrados para criar o agendamento + cancelamento).

## FASE 4/5 — Estoque, Ordens de Serviço, Notificações e Relatórios

Endpoints protegidos por sessão + RBAC. Novas permissões adicionadas ao catálogo —
**rode `python -m app.db.seed` de novo** para elas passarem a existir no banco e serem associadas
aos papéis: `stock.read/create/adjust`, `work_orders.read/create/update/cancel`, `reports.read`,
`notifications.manage`. Nova migration `migrations/versions/0005_*` (RLS incluído).

### Estoque

- `GET /api/stock` — lista com busca (`q`) por SKU/nome, filtro `only_low_stock` e `is_active`.
- `POST /api/stock` / `PATCH /api/stock/{id}` — cadastro e edição (SKU único por empresa).
- `POST /api/stock/{id}/adjust` — ajuste manual de quantidade (`IN`/`OUT`/`ADJUSTMENT`), sempre
  gravando um `StockMovement` com o motivo — nunca altera `quantity` "solto".
- `GET /api/stock/{id}/movements` — histórico de movimentações do item.
- Um item entra em "estoque crítico" quando `quantity <= min_quantity` (calculado na leitura, não
  armazenado).

### Ordens de Serviço

- `GET/POST /api/work-orders`, `GET/PATCH /api/work-orders/{id}` — CRUD com itens (`PART` vinculado
  opcionalmente a um item de estoque, ou `SERVICE` avulso).
- `POST /api/work-orders/{id}/items` / `DELETE .../items/{id}` — adiciona/remove item enquanto a OS
  não estiver `DONE`/`CANCELLED`.
- `POST /api/work-orders/{id}/close` — conclui a OS: **baixa automaticamente do estoque** cada peça
  vinculada a um `StockItem` (rejeita com 422 se não houver saldo suficiente, sem baixar nada
  parcialmente) e **dispara o comprovante** por e-mail e WhatsApp (ver Notificações abaixo).
- `POST /api/work-orders/{id}/cancel` — cancela sem baixar estoque.
- Uma OS `DONE`/`CANCELLED` não pode mais ser editada, nem fechada de novo (idempotência simples
  por status).

### Notificações (comprovante de OS e alerta de revisão)

Serviço em `app/services/notifications.py`, com envio "best-effort": sem `SMTP_*`/`WHATSAPP_*`
configurados no `.env`, cada tentativa fica registrada em `NotificationLog` com status `SKIPPED` —
**nunca** derruba a requisição que disparou o envio (ex.: fechar uma OS funciona mesmo sem e-mail
configurado ainda em produção).

- Ao fechar uma OS: envia valor total, material usado e data da próxima revisão, por e-mail e
  WhatsApp, para o cliente.
- `POST /api/notifications/check-revisions` — varre as OS concluídas com `next_revision_date`
  dentro dos próximos `REVISION_REMINDER_DAYS_AHEAD` dias (7 por padrão) e ainda não lembradas,
  envia "sua revisão está prestes a vencer" e marca para não duplicar. **Não há agendador
  embutido** neste scaffold — este endpoint é pensado para ser chamado por um cron/worker externo.
- `GET /api/notifications` — log de todas as tentativas (enviadas ou não), para auditoria.

### Relatórios (dashboard)

- `GET /api/reports/dashboard` — valor em estoque, itens críticos, OS em aberto, total de clientes
  e novos no mês, receita/lucro do mês atual vs. anterior, e uma série mês a mês (`months`,
  padrão 6) para o gráfico de comparação.
- Lucro é uma aproximação didática: receita menos custo das peças usadas (`StockItem.cost_price`
  no momento da consulta); mão de obra é tratada como 100% de margem, já que o sistema ainda não
  tem custo de mecânico/folha de pagamento.

Telas correspondentes no frontend: abas "Estoque" (lista + ajuste de quantidade), "Ordens de
serviço" (criação com itens de peça/serviço + concluir/cancelar) e "Relatórios" (cards de
indicadores + gráfico de receita/lucro por mês); os cards da tela inicial (Dashboard) também
passaram a usar esses números reais em vez de valores fixos.

## FASE 6 — Financeiro e Caixa

Endpoints protegidos por sessão + RBAC. Novas permissões: `finance.read/create/pay/cancel` e
`cash.manage` (**rode `python -m app.db.seed` de novo**). Nova migration `migrations/versions/0006_*`
(RLS incluído).

### Contas a pagar/receber (`FinanceEntry`)

- `GET /api/finance/entries` — lista com filtro por `type` (`PAYABLE`/`RECEIVABLE`), `status`
  (inclui `OVERDUE`, calculado na leitura — não é um estado gravado à parte) e período de
  vencimento (`due_before`/`due_after`).
- `POST /api/finance/entries` / `PATCH /api/finance/entries/{id}` — cria/edita (só enquanto
  `PENDING`).
- `POST /api/finance/entries/{id}/pay` — registra pagamento/recebimento, total ou parcial
  (`amount` opcional — se omitido, quita o saldo inteiro). Se houver uma sessão de caixa aberta,
  lança automaticamente o `CashMovement` correspondente (entrada para `RECEIVABLE`, saída para
  `PAYABLE`) — dá pra desligar com `register_cash_movement: false`.
- `POST /api/finance/entries/{id}/cancel` — cancela (não permitido se já `PAID`).
- **Integração automática**: ao fechar uma Ordem de Serviço (`POST /work-orders/{id}/close`, FASE
  4/5), uma `RECEIVABLE` pendente é criada automaticamente com o valor total da OS, vencimento
  imediato e vínculo em `work_order_id`.

### Caixa (`CashSession` + `CashMovement`)

- `POST /api/cash/sessions/open` — abre uma sessão com valor inicial; só pode haver **uma sessão
  `OPEN` por vez** por empresa (checado na rota).
- `POST /api/cash/sessions/{id}/close` — fecha, registrando o saldo esperado (abertura + soma dos
  movimentos) e o saldo contado fisicamente; a diferença entre os dois (`cash_difference`) é a
  quebra de caixa, para mais ou para menos.
- `GET /api/cash/sessions/current` — sessão aberta no momento (`null` se não houver).
- `POST /api/cash/sessions/{id}/movements` — movimento manual (reforço/sangria); rejeita saída
  maior que o saldo disponível. Recebimentos/pagamentos de contas não passam por aqui — eles vêm
  automaticamente do `POST /finance/entries/{id}/pay`.
- `GET /api/cash/sessions` / `GET /api/cash/sessions/{id}/movements` — histórico.

O dashboard (`GET /api/reports/dashboard`, FASE 4/5) ganhou três campos novos:
`receivables_pending`, `payables_pending` (soma do saldo em aberto de cada tipo, `PENDING` inclui
`OVERDUE`) e `cash_balance` (saldo da sessão de caixa aberta agora, ou `null` se não houver
nenhuma).

Tela correspondente no frontend: aba "Financeiro", com duas sub-abas — "Contas a pagar/receber"
(lista com filtro por tipo, criação, quitação total e cancelamento) e "Caixa" (abrir/fechar sessão,
lançar reforço/sangria manual, ver histórico de movimentações da sessão atual).

## FASE 7 — Compras e Fornecedores

Endpoints protegidos por sessão + RBAC. Novas permissões: `suppliers.read/create` e
`purchases.read/create/update/receive/cancel` (**rode `python -m app.db.seed` de novo**). Nova
migration `migrations/versions/0007_*` (RLS incluído).

### Fornecedores (`Supplier`)

- `GET /api/suppliers` — lista com busca (`q`) por nome/documento e filtro `is_active`.
- `POST /api/suppliers` / `PATCH /api/suppliers/{id}` — cadastro e edição.

### Pedidos de Compra (`PurchaseOrder`)

- `GET/POST /api/purchase-orders`, `GET/PATCH /api/purchase-orders/{id}` — CRUD com itens, cada um
  podendo (ou não) estar vinculado a um item de estoque existente.
- `POST /api/purchase-orders/{id}/receive` — recebe a mercadoria: **dá entrada automaticamente no
  estoque** de cada item vinculado a um `StockItem` (um `StockMovement` `IN` por item, mesmo padrão
  de auditoria da FASE 4/5) e **gera automaticamente a conta a pagar** (`FinanceEntry` `PAYABLE`,
  FASE 6) com o valor total do pedido e o `payment_due_date` informado na criação (ou a data do
  recebimento, se omitido). Rejeita pedidos sem itens.
- `POST /api/purchase-orders/{id}/cancel` — cancela sem mexer em estoque ou financeiro.
- Um pedido `RECEIVED`/`CANCELLED` não pode mais ser editado, recebido ou cancelado de novo.

Isso fecha o ciclo simétrico ao da OS: **OS concluída → conta a receber** (FASE 6) e **pedido de
compra recebido → conta a pagar** (FASE 7), ambos automáticos.

Tela correspondente no frontend: aba "Compras", com criação de pedido (escolhendo item já
cadastrado no estoque ou um item avulso, e cadastro rápido de fornecedor sem sair do formulário) e
ações de receber/cancelar.

## FASE 8 — Trilha de Auditoria

A permissão `audit.read` já existia no catálogo de RBAC desde a FASE 1, mas nada a populava — esta
fase fecha essa lacuna. Nova migration `migrations/versions/0008_*` (RLS incluído). Não precisa
rodar o seed de novo (a permissão já existia; nenhuma nova foi criada).

### `AuditLog` — somente leitura, só cresce

- `app/services/audit.py` expõe `log_action(...)`, chamado a partir das próprias rotas de negócio
  **depois** que a ação principal já foi commitada — se a auditoria falhar, isso nunca desfaz nem
  bloqueia a ação de negócio, e vice-versa.
- `GET /api/audit-logs` — única rota, protegida por `audit.read`; filtra por `action`,
  `entity_type` e `user_id`. Não existe `POST`/`PATCH`/`DELETE`: a aplicação nunca edita ou apaga
  uma linha já gravada.

### Ações instrumentadas nesta fase

`auth.login`, `auth.logout`, `work_order.close`, `work_order.cancel`, `finance_entry.pay`,
`finance_entry.cancel`, `cash_session.open`, `cash_session.close`, `stock.adjust`,
`purchase_order.receive`, `purchase_order.cancel` — o critério foi cobrir acesso (login/logout) e
toda transição que move dinheiro ou estoque. Novas ações sensíveis adicionadas em fases futuras
devem seguir o mesmo padrão: uma chamada a `log_action` logo após o `db.commit()` da ação
principal.

Tela correspondente no frontend: aba "Auditoria", lista somente-leitura com filtro por ação,
mostrando quando, quem, em qual entidade e o detalhe registrado.

## FASE 9 — LGPD (exportação de dados e anonimização)

Nova permissão `lgpd.manage` (ADMIN e MANAGER por padrão — **rode `python -m app.db.seed` de
novo**). Nova migration `migrations/versions/0009_*` (só adiciona colunas a `customers`, sem
tabela nova nem mudança de RLS).

### Exportação de dados (direito de acesso/portabilidade, art. 15/18)

- `GET /api/customers/{id}/export-data` — retorna tudo o que o sistema guarda sobre aquele
  cliente: cadastro, veículos, agendamentos, ordens de serviço (com itens), lançamentos
  financeiros e histórico de notificações. Fica registrado em `customer.export_data` na trilha de
  auditoria (FASE 8).

### Anonimização (direito de exclusão, art. 18)

- `POST /api/customers/{id}/anonymize` — sobrescreve nome, documento, telefone, e-mail e
  observações do cliente (`is_anonymized=true`, `is_active=false`). **Não apaga nem desvincula os
  registros de negócio** (veículos, agendamentos, OS, financeiro) — eles frequentemente têm prazo
  legal de guarda contábil/fiscal que a própria LGPD, no art. 16, reconhece como motivo válido
  para reter dados além do pedido de eliminação. Fica registrado em `customer.anonymize` na
  trilha de auditoria. Ação irreversível — o frontend pede confirmação antes de chamar.

Tela correspondente no frontend: na aba "Clientes", cada linha ganhou os botões "Exportar dados"
(baixa um `.json` com o pacote completo) e "Anonimizar" (com confirmação); um cliente já
anonimizado exibe um selo "Anonimizado" e perde essas ações.

## FASE 10 — Retenção de dados

Reaproveita a permissão `lgpd.manage` da FASE 9 (nenhuma permissão nova — não precisa rodar o
seed de novo). Nenhuma migration nova (nenhuma tabela ou coluna criada). Duas configurações novas
em `.env`/`Settings`: `RETENTION_NOTIFICATION_LOGS_DAYS` (padrão 180) e
`RETENTION_INACTIVE_CUSTOMER_YEARS` (padrão 5).

Complementa a FASE 9 com o princípio de minimização da LGPD (art. 6º, VII): não reter dado
pessoal além do necessário para a finalidade do tratamento. Sem agendador embutido neste scaffold
(mesmo padrão de `check_upcoming_revisions` da FASE 4/5) — pensado para ser chamado por um
cron/worker externo, ou manualmente pela tela.

- `GET /api/retention/candidates` — lista clientes ainda não anonimizados, sem nenhuma atividade
  (agendamento ou OS) nos últimos `RETENTION_INACTIVE_CUSTOMER_YEARS` anos e sem lançamento
  financeiro em aberto. Só lista, não altera nada.
- `POST /api/retention/purge-notifications` — apaga `NotificationLog` mais antigos que
  `RETENTION_NOTIFICATION_LOGS_DAYS` (são só registros operacionais de tentativa de envio, sem
  valor de guarda legal, e carregam `customer_id`).
- `POST /api/retention/anonymize-inactive` — anonimiza em massa todo cliente que aparece em
  `GET /retention/candidates`, usando o mesmo `anonymize_customer` da FASE 9. Cada anonimização
  fica registrada na trilha de auditoria.

Tela correspondente no frontend: aba "Retenção", com os botões "Apagar notificações antigas" e
"Anonimizar todos os candidatos" (com confirmação), e uma tabela com os clientes candidatos
(nome, última atividade, cliente desde).

## FASE 11 — Fila de notificações com retry/backoff e idempotência

Reaproveita a permissão `notifications.manage` já existente (nenhuma permissão nova). Nova
migration `migrations/versions/0010_*` (tabela `notification_requests`, com RLS).

O caminho feliz continua exatamente como nas FASES 4/5: fechar uma OS ou o alerta de revisão
tentam enviar por e-mail e WhatsApp **na hora**, de forma síncrona. A novidade é o que acontece
quando esse envio imediato **falha** (erro real de SMTP/API — não "sem configuração", que
continua caindo em `SKIPPED` e nunca entra na fila, já que retentar não resolveria):

- A falha é automaticamente enfileirada em `NotificationRequest`, com uma `idempotency_key`
  única por empresa (ex.: `work_order:42:receipt:email`) — chamar a rota que disparou o envio de
  novo (ex.: tentar fechar a mesma OS outra vez) nunca duplica a entrada na fila.
- `POST /api/notifications/process-queue` — puxa o lote de notificações cujo horário de nova
  tentativa já chegou, tenta reenviar, e:
  - sucesso → status `SENT`;
  - falhou de novo mas ainda não bateu no limite de tentativas → status `FAILED`, agenda a
    próxima tentativa com backoff exponencial (1, 2, 4, 8, 16... minutos, teto de 60min);
  - esgotou as tentativas (padrão 5) → status `GIVEN_UP`, para de tentar.
  - Cada tentativa (sucesso ou falha) também grava um `NotificationLog`, como no envio imediato.
- `GET /api/notifications/queue` — lista o estado atual da fila (pendentes, em retry, desistidas).
- Sem agendador embutido neste scaffold (mesmo padrão de `check_upcoming_revisions` e da FASE
  10): as rotas acima são pensadas para ser chamadas por um cron/worker externo, ou manualmente.

Tela correspondente no frontend: aba "Fila de notificações", com a lista de tentativas pendentes/
falhas/desistidas (canal, status, tentativas, próximo horário, último erro) e o botão "Reprocessar
fila agora".

## FASE 12 — Barramento de eventos

Sem tabela nova, sem migration, sem permissão nova — é só uma mudança de organização de código no
backend (nenhuma tela nova no frontend; o comportamento observável é idêntico ao de antes desta
fase).

`app/core/events.py` implementa `subscribe(evento, handler)` e `publish(evento, **payload)`: um
barramento **síncrono e em processo** (não é uma fila real entre processos — isso já existe para
notificações que falham, ver FASE 11). Uma exceção num handler é logada e isolada, nunca derruba
quem publicou o evento nem impede os outros handlers do mesmo evento de rodar — mesmo princípio de
resiliência já usado em notificações e auditoria.

`app/events/handlers.py` registra as reações (chamado uma vez em `app/main.py`, via
`register_handlers()`, idempotente). Primeiro (e único, por ora) call site convertido:
`POST /work-orders/{id}/close` não chama mais `notify_work_order_receipt` diretamente — publica
`work_order.closed`, e um handler inscrito nesse evento é quem dispara o comprovante. "Fechar uma
OS" não precisa mais saber que isso envia um e-mail; só publica o fato.

Para reagir a um evento novo no futuro (ex.: `customer.anonymized`, `finance_entry.paid`), basta
escrever o handler e registrar em `register_handlers()` — a rota que publica o evento não muda.

## FASE 13 — Checklist de inspeção veicular

Item pendente do P1 (orçamento/OS/checklist) desde a especificação original.

`WorkOrderChecklistItem` (migration `0011`, com RLS): item de checklist dentro de uma OS —
descrição livre, status (`NOT_CHECKED`/`OK`/`ATTENTION`), observação, quem marcou e quando. Sem
preço nem quantidade — é só um veredito de inspeção, separado de `WorkOrderItem` (que é peça/serviço
cobrado).

Rotas novas, todas reaproveitando a permissão `work_orders.update` já existente (sem permissão nova
no RBAC): `POST/PATCH/DELETE /api/work-orders/{id}/checklist(/{item_id})`. `checklist_items` vem
junto na resposta de `GET /api/work-orders/{id}`. Mesma regra de "OS encerrada" das demais edições
de OS: `DONE`/`CANCELLED` bloqueia adicionar e remover item (editar status/observação de item já
existente também fica bloqueado no frontend, que usa o mesmo status da OS para decidir).

Frontend: botão "Checklist" em cada linha da tabela de Ordens de Serviço, abre um modal com a lista
de itens, botões de status e campo de observação — some o botão de adicionar quando a OS está
encerrada.

Testes em `backend/tests/test_checklist.py`: adicionar/listar, atualizar status e observação,
remover, 404 para item inexistente, bloqueio em OS encerrada, RECEPTION sem permissão, isolamento
por empresa (RLS).

## FASE 14 — Kanban com cards arrastáveis (Ordens de Serviço + Agenda)

Sem tabela nova, sem migration, sem rota nova no backend — as duas telas passaram a usar as rotas
`PATCH` que já existiam (`/work-orders/{id}` e `/appointments/{id}`, essa última já reavalia
conflito de horário) para mudar o status ao soltar o card numa coluna diferente.

Drag-and-drop nativo do HTML5 (`draggable`, `onDragStart`/`onDragOver`/`onDrop`), sem biblioteca
nova — este ambiente não tinha acesso à internet para `npm install` no momento da implementação.

- **Ordens de serviço**: colunas Aberta → Em andamento → Aguardando aprovação → Aprovada →
  Concluída → Cancelada. Soltar em "Concluída" chama `POST /close` (checa estoque); soltar em
  "Cancelada" chama `POST /cancel`; as demais colunas fazem `PATCH {status}`. Card mostra cliente,
  placa, total e o botão de Checklist da FASE 13.
- **Agenda**: colunas Agendado → Confirmado → Em andamento → Concluído → Cancelado → Não
  compareceu. Soltar em "Cancelado" chama `POST /cancel`; as demais fazem `PATCH {status}` (o
  backend reavalia conflito de horário/mecânico automaticamente).
- Cards de itens já encerrados (`DONE`/`CANCELLED`/`NO_SHOW`) não são arrastáveis. Coluna sob o
  cursor fica destacada durante o arraste.

## Modo memória

Para testes, deixe:

```env
LLM_ENABLED=false
MEMORY_MODE=true
```

O endpoint `/api/ai/ask` primeiro procura uma resposta no `backend/data/memory.db`.
Se encontrar, não chama nenhuma LLM.

Para cadastrar uma resposta de teste:

```bash
curl -X POST http://localhost:8000/api/ai/memory \
  -H "Content-Type: application/json" \
  -d '{"question":"qual o status da ordem 1001?","answer":"A OS 1001 está em diagnóstico.","context":"demo"}'
```

Depois a mesma pergunta pode ser respondida pela memória sem custo de token.

## RAG

Fluxo:

`upload -> extração/OCR -> chunking -> índice local -> recuperação -> contexto -> LLM`

O MVP usa busca lexical local para não depender de uma API de embeddings durante desenvolvimento.
O contrato `EmbeddingProvider` já está isolado para trocar por pgvector + embeddings depois.

Endpoint:

`POST /api/rag/ingest`

Form-data: `file=<arquivo>`

Consulta:

`POST /api/ai/ask`

```json
{
  "question": "Quais serviços aparecem no documento?",
  "use_rag": true,
  "memory_first": true
}
```

## LLMs

Configure uma destas opções:

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-4.1-mini
```

ou Anthropic:

```env
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=...
ANTHROPIC_MODEL=claude-3-5-haiku-latest
```

ou Gemini:

```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=...
GEMINI_MODEL=gemini-2.0-flash
```

ou Ollama local:

```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

O código nunca coloca chaves no frontend.

## Estrutura

```text
oficina-ai/
├─ backend/
│  ├─ app/
│  │  ├─ api/
│  │  ├─ core/
│  │  ├─ db/
│  │  ├─ models/
│  │  ├─ schemas/
│  │  ├─ services/
│  │  │  ├─ ai/
│  │  │  ├─ rag/
│  │  │  ├─ ocr/
│  │  │  └─ memory/
│  │  └─ main.py
│  ├─ data/
│  └─ requirements.txt
├─ frontend/
│  ├─ src/
│  │  ├─ components/
│  │  ├─ pages/
│  │  └─ lib/
│  └─ package.json
├─ docs/
│  ├─ ARCHITECTURE.md
│  ├─ AI-RAG-OCR.md
│  ├─ SECURITY.md
│  └─ ROADMAP.md
├─ docker-compose.yml
└─ .env.example
```

## Próximas fases

1. ~~Auth/sessões/RBAC + multiempresa real~~ (FASE 1, concluída)
2. ~~Clientes/veículos~~ (FASE 2, concluída)
3. ~~Agenda~~ (FASE 3, concluída)
4. ~~Orçamento/OS/checklist~~ (FASE 4/5 orçamento/OS; FASE 13 checklist — concluído)
5. ~~Estoque/transações/concorrência~~ (FASE 4/5, concluída)
6. ~~Financeiro/caixa~~ (FASE 6, concluída)
7. ~~Notificações/fila/WhatsApp/e-mail~~ (FASE 4/5 envio; FASE 11 fila/retry, concluídas)
8. ~~Auditoria/LGPD/exportação~~ (FASE 8/9/10, concluídas)
9. Observabilidade/backup/hardening — em aberto, ver `docs/ROADMAP.md` (P4)
10. pgvector + embeddings — em aberto, ver `docs/ROADMAP.md` (P5)
11. suíte E2E e CI/CD — em aberto
