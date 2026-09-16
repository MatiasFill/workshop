# Arquitetura

## Camadas

Frontend → API FastAPI → serviços/use cases → persistência/integrations.

AI:
`request -> memory lookup -> RAG retrieval -> prompt builder -> LLM adapter -> memory save`

O gateway não conhece detalhes do frontend e os providers não são chamados diretamente por telas.

## Evolução

A fundação foi desenhada para migrar a recuperação lexical para pgvector sem mudar o contrato da API.
Também permite adicionar providers sem acoplar o domínio a uma LLM.

## Multiempresa

A especificação exige `company_id` derivado da sessão, nunca confiado ao frontend.
O scaffold ainda não considera esta parte pronta: a próxima fase deve criar contexto de tenant,
RBAC e testes de isolamento antes de uso produtivo.
