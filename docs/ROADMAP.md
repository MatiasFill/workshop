# Roadmap alinhado à especificação

## P0 — Fundação
- [x] Python/FastAPI
- [x] PostgreSQL/pgvector no Docker
- [x] RAG básico
- [x] OCR de imagem
- [x] Memory-first
- [x] Gateway multi-LLM
- [x] UI Tailwind

## P1 — Core de negócio
- [x] Company/Branch/User/Role/Permission (FASE 1)
- [x] sessão segura (FASE 1)
- [x] clientes/veículos (FASE 2)
- [x] agenda (FASE 3)
- [x] orçamento/OS/checklist (FASE 4/5 — ver Ordens de Serviço abaixo)

## P2 — Operação
- [x] estoque transacional (FASE 4/5: StockItem + StockMovement, baixa automática ao fechar OS)
- [x] compras/fornecedores (FASE 7: Supplier + PurchaseOrder/PurchaseOrderItem, recebimento dá entrada no estoque e gera FinanceEntry PAYABLE automaticamente)
- [x] financeiro/caixa (FASE 6: FinanceEntry a pagar/receber + CashSession/CashMovement)
- [x] revisões (FASE 4/5: alerta "revisão prestes a vencer", ver notifications.check_upcoming_revisions)

## P3 — Comunicação
- [x] eventos (FASE 12: barramento síncrono em processo — app/core/events.py — desacoplando "isso aconteceu" de "faça isso a respeito")
- [x] fila (FASE 11: NotificationRequest — fila de reenvio para o que falhou no envio imediato)
- [x] retry/backoff (mesma FASE 11: backoff exponencial 1/2/4/8/16... min, teto 60min, até 5 tentativas)
- [x] WhatsApp (FASE 4/5: envio best-effort via API HTTP configurável, SKIPPED sem credenciais)
- [x] e-mail (FASE 4/5: comprovante de OS via SMTP, SKIPPED sem credenciais)
- [x] idempotência (mesma FASE 11: `idempotency_key` única por empresa, nunca duplica o reenvio)

## P4 — Governança
- [x] audit log (FASE 8: AuditLog + serviço append-only, instrumentado em login/logout, OS, financeiro, caixa, estoque e compras)
- [x] LGPD (FASE 9: exportação de dados do cliente e anonimização — direitos de acesso/portabilidade e exclusão, art. 15/18)
- [x] exportação/anonymização (mesma FASE 9)
- [x] retenção (FASE 10: purga de NotificationLog antigos + anonimização em massa de clientes inativos sem pendência financeira, princípio de minimização art. 6º VII)
- [ ] monitoramento
- [ ] backup/restore

## Próximos passos sugeridos (pós FASE 12)
- Agendador real (cron/worker) para `check_upcoming_revisions`,
  `POST /retention/purge-notifications`, `POST /retention/anonymize-inactive`
  e `POST /notifications/process-queue` — todos hoje disparados manualmente.
- Página de checklist de inspeção veicular dentro da Ordem de Serviço.
- Monitoramento e backup/restore seguem em aberto no P4; todo o P5 (IA
  avançada) segue não iniciado.
- Todo o P3 (Comunicação) está concluído — próximos handlers de evento
  (ex.: `customer.anonymized`, `finance_entry.paid`) podem ser adicionados
  em app/events/handlers.py sem tocar nas rotas que já publicam esses
  eventos, se algum dia fizer sentido reagir a eles.


## P5 — AI avançada
- [ ] pgvector/embeddings
- [ ] reranker
- [ ] citações por página
- [ ] memória semântica
- [ ] avaliação de respostas
- [ ] controle de custo por tenant
