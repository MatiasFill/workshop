# AI, RAG, OCR e memória

## Memory-first

Toda pergunta passa primeiro pelo cache persistente local quando `MEMORY_MODE=true`.
A chave é um hash da pergunta + contexto. Isso é proposital para testes repetitivos.

## RAG

Documentos são convertidos em texto, divididos em chunks e persistidos.
A recuperação inicial é lexical e local para reduzir dependência de APIs.

## OCR

Imagens passam pelo Tesseract quando disponível.
Para PDFs digitais usamos PyMuPDF; PDFs escaneados podem receber OCR em uma evolução
com renderização de página + Tesseract.

## Providers

Há adapters para OpenAI, Anthropic, Gemini e Ollama.
O segredo fica somente no backend.

## Produção

Para produção, adicionar:
- embeddings e pgvector
- reranking
- citações por chunk/página
- avaliação de RAG
- filtros por tenant/permissão
- redaction de dados sensíveis
- observabilidade de tokens/custo
- filas para OCR pesado
