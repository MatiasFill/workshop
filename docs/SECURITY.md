# Segurança

A especificação original exige autenticação, RBAC, isolamento multiempresa, validação backend,
auditoria, rate limiting, CSRF quando aplicável, CSP, uploads protegidos, backups e testes.

Este scaffold NÃO declara esses controles como concluídos. Antes de produção:
- implementar sessão segura
- RBAC e autorização por objeto
- tenant context no backend
- rate limiting
- validação de MIME/conteúdo de upload
- auditoria
- headers/CSP
- gestão de segredos
- backup/restore
- SAST/dependency scanning
- testes de IDOR, XSS, CSRF, webhook e concorrência
