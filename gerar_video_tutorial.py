from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import subprocess
import shutil

ROOT = Path(__file__).parent
FRAMES = ROOT / "frames_video_tutorial"
OUTPUT = Path.home() / "Downloads" / "VIDEO_TUTORIAL_OFICINA_AI.mp4"
FRAMES.mkdir(exist_ok=True)

FONT_DIR = Path("C:/Windows/Fonts")
REGULAR = FONT_DIR / "segoeui.ttf"
BOLD = FONT_DIR / "segoeuib.ttf"


def font(size, bold=False):
    return ImageFont.truetype(str(BOLD if bold else REGULAR), size)


def text(draw, xy, value, size=24, fill="#334155", bold=False, anchor=None):
    draw.text(xy, value, font=font(size, bold), fill=fill, anchor=anchor)


def rounded(draw, box, fill, radius=14, outline=None, width=1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def make_frame(index, title, subtitle, bullets, menu, active):
    image = Image.new("RGB", (1920, 1080), "#f6f8fb")
    draw = ImageDraw.Draw(image)

    # Sidebar
    draw.rectangle((0, 0, 360, 1080), fill="#ffffff")
    draw.rectangle((0, 0, 360, 96), fill="#0f172a")
    rounded(draw, (28, 26, 70, 68), "#2563eb", 12)
    text(draw, (49, 47), "W", 25, "#ffffff", True, "mm")
    text(draw, (88, 35), "Oficina AI", 25, "#ffffff", True)
    text(draw, (88, 65), "Tutorial do sistema", 14, "#cbd5e1")

    y = 130
    for item in menu:
        selected = item == active
        if selected:
            rounded(draw, (20, y - 9, 340, y + 43), "#dbeafe", 12)
        text(draw, (48, y + 16), "●", 12, "#2563eb" if selected else "#94a3b8", True, "mm")
        text(draw, (72, y + 16), item, 19, "#0f172a" if selected else "#64748b", selected, "lm")
        y += 56

    # Main content
    text(draw, (420, 82), "Oficina AI", 16, "#64748b", True)
    text(draw, (420, 125), title, 42, "#0f172a", True)
    text(draw, (420, 178), subtitle, 22, "#64748b")
    rounded(draw, (420, 230, 1840, 900), "#ffffff", 22, "#e2e8f0", 2)

    # Top action
    rounded(draw, (1570, 260, 1800, 316), "#0f172a", 12)
    text(draw, (1685, 288), "+  Nova ação", 19, "#ffffff", True, "mm")

    # Content cards and interaction labels
    card_y = 360
    for n, bullet in enumerate(bullets):
        x = 480 + (n % 2) * 650
        yb = card_y + (n // 2) * 170
        rounded(draw, (x, yb, x + 570, yb + 125), "#f8fafc", 16, "#e2e8f0")
        text(draw, (x + 28, yb + 28), f"{n + 1:02d}", 19, "#2563eb", True)
        text(draw, (x + 84, yb + 28), bullet, 22, "#0f172a", True)
        text(draw, (x + 28, yb + 73), "Clique para consultar e atualizar", 16, "#64748b")

    # Tutorial overlay
    rounded(draw, (420, 930, 1840, 1015), "#eff6ff", 14, "#bfdbfe")
    text(draw, (450, 972), "INTERAÇÃO:", 17, "#1d4ed8", True, "lm")
    text(draw, (610, 972), subtitle, 17, "#1e3a8a", False, "lm")
    rounded(draw, (1740, 935, 1815, 1010), "#ef4444", 38)
    text(draw, (1777, 973), "▶", 26, "#ffffff", True, "mm")
    text(draw, (420, 1045), f"Tutorial Oficina AI  •  Cena {index:02d}", 15, "#94a3b8")
    return image


menu = [
    "Dashboard", "Agenda", "Clientes", "Veículos", "Ordens de serviço",
    "Estoque", "Compras", "Financeiro", "Relatórios", "Auditoria",
    "Retenção", "Notificações",
]

scenes = [
    ("Bem-vindo à Oficina AI", "Conheça o sistema menu por menu", ["Login seguro", "Operação completa", "Gestão em um só lugar"], "Dashboard"),
    ("Dashboard", "Comece pela visão geral da oficina", ["Indicadores do dia", "Clientes e atendimentos", "Alertas importantes"], "Dashboard"),
    ("Agenda", "Crie um atendimento: cliente, veículo, data e horário", ["Novo agendamento", "Selecionar cliente", "Definir horário"], "Agenda"),
    ("Clientes", "Cadastre e pesquise clientes por nome ou documento", ["Buscar cliente", "Novo cadastro", "Dados de contato"], "Clientes"),
    ("Veículos", "Associe um ou mais veículos ao cliente", ["Placa normalizada", "Marca e modelo", "Histórico do veículo"], "Veículos"),
    ("Ordens de serviço", "Abra, acompanhe e conclua serviços", ["Nova ordem", "Itens e serviços", "Status do atendimento"], "Ordens de serviço"),
    ("Estoque", "Controle peças, quantidades e estoque mínimo", ["Pesquisar item", "Entrada e saída", "Estoque crítico"], "Estoque"),
    ("Compras", "Gerencie fornecedores e pedidos de compra", ["Novo fornecedor", "Criar pedido", "Registrar recebimento"], "Compras"),
    ("Financeiro e Caixa", "Registre entradas, saídas e fechamento", ["Abrir caixa", "Movimentações", "Fechar caixa"], "Financeiro"),
    ("Relatórios", "Analise indicadores e evolução da oficina", ["Resumo operacional", "Indicadores financeiros", "Série mensal"], "Relatórios"),
    ("Auditoria", "Consulte quem fez cada alteração", ["Usuário", "Data e hora", "Ação registrada"], "Auditoria"),
    ("Retenção de dados", "Trate dados antigos conforme a LGPD", ["Candidatos", "Anonimização", "Conformidade"], "Retenção"),
    ("Fila de notificações", "Acompanhe mensagens pendentes e processadas", ["Fila pendente", "Processar fila", "Status do envio"], "Notificações"),
    ("Encerramento", "Saia com segurança ao terminar", ["Revisar operação", "Salvar alterações", "Encerrar sessão"], "Dashboard"),
]

for i, (title_value, subtitle_value, bullets, active) in enumerate(scenes, start=1):
    frame = make_frame(i, title_value, subtitle_value, bullets, menu, active)
    frame.save(FRAMES / f"frame_{i:03d}.png")

ffmpeg = shutil.which("ffmpeg")
if not ffmpeg:
    candidates = list(Path("C:/Program Files").glob("ffmpeg*/bin/ffmpeg.exe"))
    if candidates:
        ffmpeg = str(candidates[0])
if not ffmpeg:
    raise SystemExit("FFmpeg não encontrado após a instalação.")

if OUTPUT.exists():
    OUTPUT.unlink()

subprocess.run(
    [
        ffmpeg, "-y", "-framerate", "1/4", "-i", str(FRAMES / "frame_%03d.png"),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        str(OUTPUT),
    ],
    check=True,
)
print(OUTPUT)
