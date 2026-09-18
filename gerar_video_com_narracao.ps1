$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$frames = Join-Path $root "frames_video_tutorial"
$downloads = Join-Path $env:USERPROFILE "Downloads"
$wav = Join-Path $downloads "NARRACAO_VIDEO_TUTORIAL_OFICINA_AI.wav"
$audio = Join-Path $downloads "NARRACAO_VIDEO_TUTORIAL_OFICINA_AI.m4a"
$mp4 = Join-Path $downloads "VIDEO_TUTORIAL_OFICINA_AI_COM_AUDIO.mp4"
$ffmpegDir = "C:\Users\MatiasFill\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg.Shared_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.1-full_build-shared\bin"
$ffmpeg = Join-Path $ffmpegDir "ffmpeg.exe"

if (-not (Test-Path $ffmpeg)) {
  throw "FFmpeg não encontrado em $ffmpeg"
}

Add-Type -AssemblyName System.Speech
$voice = New-Object System.Speech.Synthesis.SpeechSynthesizer
$voice.SelectVoice("Microsoft Maria Desktop")
$voice.Rate = -1
$voice.Volume = 100

$script = @"
Bem-vindo à Oficina AI. Neste tutorial, vamos conhecer o sistema completo, desde o cadastro do cliente e do veículo até o controle financeiro da oficina.

Começamos pelo login. Informe seu e-mail e sua senha e clique em Entrar. O sistema abre os menus de acordo com as permissões do seu usuário.

No Dashboard, você encontra a visão geral da oficina. Consulte clientes, atendimentos, ordens de serviço, alertas de estoque e os principais indicadores da operação.

Agora vamos cadastrar um cliente. Abra o menu Clientes, clique em Novo cliente e informe nome, CPF ou CNPJ, telefone e e-mail. Depois, clique em Salvar cliente.

Para cadastrar o carro, abra a ficha do cliente e adicione o veículo. Informe a placa, marca e modelo. Um cliente pode ter vários veículos, e cada um fica ligado ao seu histórico.

Na Agenda, clique em Novo agendamento. Pesquise o cliente, selecione o veículo, escolha a data e o horário, informe a duração e descreva o serviço. Clique em Agendar.

Quando o carro chegar, abra Ordens de serviço. Selecione cliente e veículo, descreva o problema, inclua serviços e peças, e salve a ordem. Atualize o status durante o atendimento.

No Estoque, consulte peças e materiais, veja a quantidade atual e o estoque mínimo. Para cadastrar material, clique em Novo item, informe nome, unidade e quantidade, e salve.

Quando houver entrada ou consumo, faça um ajuste de estoque com a quantidade e o motivo. Os alertas de estoque crítico ajudam a planejar novas compras.

Em Compras, cadastre fornecedores, crie um pedido, selecione os materiais e quantidades e acompanhe o status. Quando a entrega chegar, registre o recebimento para atualizar o estoque.

No Financeiro, registre contas, receitas e despesas. Informe o tipo de movimentação, valor, descrição e data. Depois, acompanhe os pagamentos e os valores em aberto.

No Caixa, abra a sessão informando o valor inicial. Registre cada entrada e saída durante o dia. No encerramento, confira o saldo e clique em Fechar caixa.

Em Relatórios, consulte os indicadores de clientes, serviços, estoque e financeiro. Use os dados para acompanhar resultados e tomar decisões sobre a oficina.

A Auditoria mostra quem realizou cada ação, quando ela aconteceu e qual registro foi alterado. Retenção ajuda a tratar dados antigos conforme as regras da empresa e a LGPD.

Por fim, a Fila de notificações mostra mensagens pendentes e processadas. Ao terminar o trabalho, clique em Sair para encerrar a sessão com segurança. Agora você já conhece o fluxo completo da Oficina AI.
"@

$voice.SetOutputToWaveFile($wav)
$voice.Speak($script)
$voice.Dispose()

if (Test-Path $mp4) {
  Remove-Item -LiteralPath $mp4 -Force
}

if (Test-Path $audio) {
  Remove-Item -LiteralPath $audio -Force
}

& $ffmpeg -y -i $wav -c:a aac -b:a 128k $audio
if ($LASTEXITCODE -ne 0) {
  throw "FFmpeg não conseguiu preparar a narração."
}

& $ffmpeg -y -framerate "1/20" -i (Join-Path $frames "frame_%03d.png") -i $audio `
  -map 0:v:0 -map 1:a:0 -c:v libx264 -pix_fmt yuv420p -c:a copy `
  -t 280 -movflags +faststart $mp4

if ($LASTEXITCODE -ne 0) {
  throw "FFmpeg não conseguiu montar o vídeo."
}

Remove-Item -LiteralPath $wav -Force
Remove-Item -LiteralPath $audio -Force
Write-Output $mp4
