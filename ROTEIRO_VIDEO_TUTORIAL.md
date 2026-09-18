# Roteiro do vídeo tutorial — Oficina AI

## Objetivo

Ensinar um usuário novo a entrar no sistema e executar as principais tarefas,
menu por menu, mostrando cada interação na tela.

## Formato recomendado

- **Duração:** 8 a 12 minutos
- **Formato:** gravação de tela em 16:9, com narração
- **Resolução:** 1920 x 1080
- **Ritmo:** cursor destacado, zoom curto nos formulários e pausa de 1 segundo após cada ação
- **Dados:** usar dados fictícios de demonstração; nunca gravar senhas, CPF/CNPJ ou dados reais

## Preparação antes da gravação

1. Iniciar o backend, banco, Redis e frontend.
2. Criar ou separar um usuário de demonstração.
3. Confirmar que há pelo menos um cliente, um veículo, um item de estoque e um fornecedor de teste.
4. Abrir o sistema no navegador em `http://localhost:5173`.
5. Ativar gravação do cursor e do teclado.
6. Limpar notificações e deixar a tela inicial pronta.

---

## Cena 1 — Abertura

**Tempo:** 0:00–0:20

**Tela:** página de login da Oficina AI.

**Narração:**

> Neste vídeo, vamos aprender a usar a Oficina AI na prática. Vou mostrar o
> login e todos os menus principais: dashboard, agenda, clientes, ordens de
> serviço, estoque, compras, financeiro, relatórios, auditoria, retenção e
> notificações.

**Ação:**

- Mostrar rapidamente a marca e a tela de login.
- Mover o cursor até os campos de e-mail e senha.

---

## Cena 2 — Login e segurança da sessão

**Tempo:** 0:20–0:45

**Ação:**

1. Clicar em **E-mail**.
2. Digitar o e-mail do usuário de demonstração.
3. Clicar em **Senha**.
4. Digitar a senha sem exibi-la na gravação.
5. Clicar em **Entrar**.

**Narração:**

> Para entrar, informe o e-mail e a senha do seu usuário. O sistema valida as
> credenciais e abre somente os menus permitidos para o seu perfil. Se houver
> erro, a mensagem aparece abaixo do formulário e os dados podem ser corrigidos.

**Demonstração opcional:**

- Mostrar rapidamente uma tentativa inválida usando dados fictícios.
- Voltar e fazer o login correto.

---

## Cena 3 — Dashboard

**Tempo:** 0:45–1:25

**Tela:** menu **Dashboard**.

**Ação:**

1. Apontar para o menu lateral.
2. Clicar em **Dashboard**.
3. Mostrar os cartões de resumo.
4. Passar o cursor pelos indicadores.
5. Mostrar gráficos e informações da operação.

**Narração:**

> O Dashboard é a central da oficina. Aqui você acompanha rapidamente os
> principais números do negócio, como clientes, atendimentos, ordens, caixa,
> estoque e indicadores do período. Use esta tela para saber o que precisa de
> atenção antes de começar a operação.

**Mensagem na tela:**

> Comece pelo Dashboard para ter uma visão geral da oficina.

---

## Cena 4 — Agenda

**Tempo:** 1:25–2:20

**Tela:** menu **Agenda**.

**Ação — criar agendamento:**

1. Clicar em **Agenda**.
2. Clicar em **Novo agendamento**.
3. No campo **Cliente**, digitar parte do nome.
4. Selecionar um resultado da lista.
5. Selecionar o veículo.
6. Escolher a data.
7. Escolher o horário.
8. Ajustar a duração em minutos.
9. Informar o tipo de serviço, por exemplo, “Revisão”.
10. Clicar em **Agendar**.
11. Confirmar o novo item na lista.

**Narração:**

> Na Agenda, o atendimento começa pela busca do cliente. Ao selecionar o
> cliente, escolha também o veículo, quando houver um veículo cadastrado.
> Depois informe data, horário, duração e serviço. Ao clicar em Agendar, o
> sistema grava o compromisso e exibe o status do atendimento.

**Ação — status e cancelamento:**

- Mostrar um agendamento com status **Agendado**.
- Explicar os status **Confirmado**, **Em andamento**, **Concluído** e
  **Cancelado**.
- Se disponível no ambiente, clicar em **Cancelar** em um registro de teste e
  atualizar a lista.

**Narração:**

> O cancelamento mantém o histórico do agendamento e libera aquele horário
> para uma nova marcação.

---

## Cena 5 — Clientes e veículos

**Tempo:** 2:20–3:20

**Tela:** menu **Clientes**.

**Ação — pesquisar:**

1. Clicar em **Clientes**.
2. Digitar nome, telefone ou documento no campo de busca.
3. Mostrar a lista filtrada.
4. Limpar a busca.

**Ação — criar cliente:**

1. Clicar em **Novo cliente**.
2. Preencher **Nome**.
3. Preencher **CPF/CNPJ** com dado fictício.
4. Preencher **Telefone** de demonstração.
5. Informar a **Placa do veículo**.
6. Clicar em **Salvar cliente**.
7. Mostrar o cliente na lista.

**Narração:**

> O menu Clientes concentra o cadastro e a busca da base da oficina. A busca
> pode ser feita por nome, documento, telefone ou e-mail. Para cadastrar,
> informe o nome e, se necessário, os dados de contato e a placa do veículo.

**Ação — ficha e veículos:**

- Abrir o cliente recém-criado.
- Mostrar os veículos associados.
- Mostrar a seleção de veículo usada na Agenda.
- Demonstrar, se disponível, a edição ou inclusão de outro veículo.

**Narração:**

> Um cliente pode ter mais de um veículo. Essa relação evita cadastros
> duplicados e permite associar cada ordem ou agendamento ao veículo correto.

---

## Cena 6 — Ordens de serviço

**Tempo:** 3:20–4:25

**Tela:** menu **Ordens de serviço**.

**Ação:**

1. Clicar em **Ordens de serviço**.
2. Clicar em **Nova ordem** ou no botão equivalente.
3. Selecionar o cliente.
4. Selecionar o veículo.
5. Informar o serviço ou problema relatado.
6. Adicionar os itens ou serviços necessários, quando disponíveis.
7. Salvar a ordem.
8. Mostrar a ordem criada na lista.
9. Alterar o status conforme o fluxo disponível.

**Narração:**

> A ordem de serviço organiza o trabalho executado pela oficina. Selecione o
> cliente e o veículo, descreva o problema ou serviço, inclua os itens
> necessários e salve. A equipe pode acompanhar a ordem desde a abertura até
> a conclusão.

**Estados para narrar, se aparecerem na tela:**

- Aberta ou pendente.
- Em andamento.
- Concluída.
- Cancelada.

**Narração:**

> Sempre atualize o status para que a recepção, a oficina e a gestão tenham a
> mesma visão do atendimento.

---

## Cena 7 — Estoque

**Tempo:** 4:25–5:15

**Tela:** menu **Estoque**.

**Ação:**

1. Clicar em **Estoque**.
2. Pesquisar um item.
3. Mostrar quantidade atual e estoque mínimo.
4. Criar um item de demonstração.
5. Informar nome, unidade, quantidade e limite mínimo.
6. Salvar.
7. Fazer um ajuste de entrada ou saída.
8. Mostrar o alerta de estoque crítico, quando aplicável.

**Narração:**

> No Estoque, a oficina controla peças e materiais. Pesquise um item para
> consultar a quantidade disponível, cadastre novos produtos e faça ajustes
> sempre que houver entrada, consumo ou correção de inventário.

**Narração adicional:**

> O estoque mínimo ajuda a identificar antecipadamente os itens que precisam
> ser comprados.

---

## Cena 8 — Compras e fornecedores

**Tempo:** 5:15–6:05

**Tela:** menu **Compras**.

**Ação — fornecedor:**

1. Clicar em **Compras**.
2. Abrir a área de fornecedores.
3. Cadastrar um fornecedor fictício.
4. Salvar e mostrar o fornecedor na lista.

**Ação — pedido:**

1. Clicar em **Novo pedido de compra**.
2. Selecionar o fornecedor.
3. Adicionar os itens.
4. Informar quantidades e valores, se solicitados.
5. Salvar o pedido.
6. Mostrar o status do pedido.
7. Clicar em **Receber** quando o material chegar.

**Narração:**

> O menu Compras conecta fornecedores, pedidos e recebimentos. Primeiro
> selecione o fornecedor, depois inclua os itens e quantidades. Quando a
> entrega chegar, registre o recebimento para atualizar o controle da compra
> e do estoque.

---

## Cena 9 — Financeiro e Caixa

**Tempo:** 6:05–7:10

**Tela:** menu **Financeiro**.

**Ação — caixa:**

1. Clicar em **Financeiro**.
2. Mostrar o estado atual do caixa.
3. Clicar em **Abrir caixa**.
4. Informar o valor inicial, se solicitado.
5. Confirmar a abertura.

**Ação — movimentação:**

1. Clicar em **Nova movimentação**.
2. Escolher entrada ou saída.
3. Informar valor.
4. Informar descrição.
5. Salvar.
6. Mostrar o saldo atualizado.

**Ação — contas:**

- Mostrar entradas e saídas financeiras.
- Mostrar uma conta em aberto.
- Demonstrar o registro de pagamento, se disponível.

**Ação — fechamento:**

1. Conferir as movimentações.
2. Clicar em **Fechar caixa**.
3. Confirmar o fechamento.
4. Mostrar o status de caixa fechado.

**Narração:**

> No Financeiro, você acompanha entradas, saídas e pagamentos. O caixa deve
> ser aberto no início da operação, receber todas as movimentações e ser
> fechado ao final do período. Isso mantém o saldo e o histórico organizados.

---

## Cena 10 — Relatórios

**Tempo:** 7:10–7:50

**Tela:** menu **Relatórios**.

**Ação:**

1. Clicar em **Relatórios**.
2. Mostrar os cartões de indicadores.
3. Mostrar a série mensal ou gráficos disponíveis.
4. Alterar o período, se houver filtro.
5. Passar o cursor por um gráfico.
6. Mostrar a leitura dos dados.

**Narração:**

> Os Relatórios transformam a operação em informação para decisão. Consulte
> os indicadores de clientes, serviços, movimentação financeira e desempenho
> ao longo do tempo. Use os filtros disponíveis para analisar um período
> específico.

---

## Cena 11 — Auditoria

**Tempo:** 7:50–8:20

**Tela:** menu **Auditoria**.

**Ação:**

1. Clicar em **Auditoria**.
2. Mostrar a lista de eventos.
3. Abrir ou expandir um registro.
4. Apontar para usuário, data, ação e recurso alterado.

**Narração:**

> A Auditoria registra as ações relevantes realizadas no sistema. Ela permite
> verificar quem fez uma alteração, quando isso aconteceu e qual recurso foi
> afetado, reforçando o controle e a rastreabilidade.

---

## Cena 12 — Retenção de dados

**Tempo:** 8:20–8:55

**Tela:** menu **Retenção**.

**Ação:**

1. Clicar em **Retenção**.
2. Mostrar candidatos a retenção ou anonimização.
3. Abrir um registro de teste.
4. Explicar o botão de anonimização.
5. Executar somente com dados fictícios, se a demonstração exigir.

**Narração:**

> O menu Retenção ajuda a tratar dados antigos ou inativos conforme as regras
> da empresa e os princípios da LGPD. Antes de executar qualquer ação,
> confira os candidatos e utilize apenas dados de demonstração durante este
> treinamento.

---

## Cena 13 — Fila de notificações

**Tempo:** 8:55–9:25

**Tela:** menu **Fila de notificações**.

**Ação:**

1. Clicar em **Fila de notificações**.
2. Mostrar itens pendentes e processados.
3. Clicar em **Processar fila**.
4. Atualizar a tela.
5. Mostrar a mudança de status.

**Narração:**

> A fila de notificações organiza as mensagens geradas pelo sistema. O usuário
> pode acompanhar o que está pendente, processar a fila e conferir o resultado
> de cada notificação.

---

## Cena 14 — Documentos e IA/RAG

**Tempo:** 9:25–10:00

**Tela:** menu **Documentos RAG**, se habilitado para o perfil.

**Ação:**

1. Clicar em **Documentos RAG**, quando o menu estiver disponível.
2. Selecionar um arquivo de demonstração.
3. Fazer o envio.
4. Mostrar o documento na lista.
5. Fazer uma pergunta no módulo de IA, se a tela estiver disponível.

**Narração:**

> Quando habilitado, o módulo de Documentos RAG permite enviar documentos
> para consulta inteligente. Depois do processamento, o usuário pode fazer
> perguntas usando o conteúdo autorizado da oficina. Nunca envie documentos
> sensíveis em uma gravação pública.

---

## Cena 15 — Encerrar sessão

**Tempo:** 10:00–10:20

**Tela:** menu lateral e botão de sair.

**Ação:**

1. Mostrar o menu lateral completo.
2. Clicar no perfil ou no botão **Sair**, **Logout** ou **Encerrar sessão**.
3. Confirmar o retorno à tela de login.

**Narração:**

> Ao terminar o trabalho, encerre a sessão pelo botão de saída. Isso protege os
> dados da oficina, principalmente em computadores compartilhados.

---

## Encerramento do vídeo

**Narração:**

> Agora você já conhece o fluxo completo da Oficina AI: começar pelo
> Dashboard, organizar a Agenda, cadastrar Clientes e Veículos, acompanhar
> Ordens de Serviço, controlar Estoque e Compras, fechar o Financeiro,
> consultar Relatórios e manter Auditoria, Retenção e Notificações em ordem.
> Consulte este tutorial sempre que precisar revisar uma etapa da operação.

**Tela final:**

- Logo Oficina AI.
- Texto: “Oficina AI — operação organizada em um só lugar”.
- Exibir por 3 segundos.

## Checklist de gravação

- [ ] Cursor visível e destacado.
- [ ] Nenhuma senha ou dado real aparece.
- [ ] Cada clique fica na tela tempo suficiente para o usuário acompanhar.
- [ ] Os nomes dos menus são narrados exatamente como aparecem.
- [ ] Erros e validações são demonstrados apenas com dados fictícios.
- [ ] A gravação mostra o resultado depois de cada ação.
- [ ] O áudio foi revisado e está sincronizado com o cursor.
- [ ] O vídeo foi exportado em MP4, H.264, 1080p.
