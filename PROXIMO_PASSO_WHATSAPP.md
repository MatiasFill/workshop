# Próximo passo: envio automatizado de PDF por WhatsApp

## Objetivo

Preparar a automação para enviar o relatório em PDF para um número de WhatsApp, sem exigir envio manual toda vez.

## Requisitos

- WhatsApp Business API ou Cloud API
- número verificado
- token de autenticação
- endpoint de envio ou biblioteca oficial de integração

## Escopo planejado

- preparar o arquivo PDF final em `RELATORIO_MUDANCAS.pdf`
- definir o número de destino e o texto da mensagem
- criar script de envio automatizado
- validar o fluxo com o número verificado
- manter o processo reutilizável para outros relatórios

## Fluxo ideal

1. gerar o PDF
2. salvar em um diretório de anexos
3. chamar a API do WhatsApp com o arquivo
4. enviar como documento ou mídia
5. registrar log de sucesso/erro

## Observações

- Isso não é possível diretamente pelo ambiente atual sem credenciais reais da API do WhatsApp.
- O envio manual pelo celular continua sendo o caminho mais simples enquanto a integração oficial não estiver configurada.
- Este passo foi registrado para execução posterior, quando a conta e credenciais estiverem disponíveis.

## Arquivos relacionados

- [RELATORIO_MUDANCAS.pdf](./RELATORIO_MUDANCAS.pdf)
- [RELATORIO_MUDANCAS.md](./RELATORIO_MUDANCAS.md)
- [PROXIMO_PASSO_KIND.md](./PROXIMO_PASSO_KIND.md)
