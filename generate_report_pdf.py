from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
import re

src = r"c:\Users\MatiasFill\Desktop\oficina-ai-fase12\oficina-ai\RELATORIO_MUDANCAS.md"
dst = r"c:\Users\MatiasFill\Desktop\oficina-ai-fase12\oficina-ai\RELATORIO_MUDANCAS.pdf"

with open(src, "r", encoding="utf-8") as f:
    lines = f.read().splitlines()

styles = getSampleStyleSheet()
story = []

for line in lines:
    stripped = line.strip()
    if not stripped:
        story.append(Spacer(1, 8))
        continue

    if stripped.startswith("# "):
        story.append(Paragraph(stripped[2:], styles["Title"]))
    elif stripped.startswith("## "):
        story.append(Paragraph(stripped[3:], styles["Heading2"]))
    elif stripped.startswith("### "):
        story.append(Paragraph(stripped[4:], styles["Heading3"]))
    elif stripped.startswith("```"):
        continue
    elif stripped.startswith("- ") or stripped.startswith("* "):
        story.append(Paragraph("• " + stripped[2:], styles["BodyText"]))
    elif re.match(r"^\d+\.\s", stripped):
        story.append(Paragraph(stripped, styles["BodyText"]))
    else:
        story.append(Paragraph(stripped, styles["BodyText"]))

pdf = SimpleDocTemplate(
    dst,
    pagesize=A4,
    leftMargin=40,
    rightMargin=40,
    topMargin=40,
    bottomMargin=40,
)
pdf.build(story)
print(f"PDF criado em: {dst}")
