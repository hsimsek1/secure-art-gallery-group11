"""Build the two PDF reports and vector diagrams from the Markdown sources.

Requires reportlab (documentation only; not an application dependency).
"""
from html import escape
from pathlib import Path
import re

from reportlab.graphics import renderSVG
from reportlab.graphics.shapes import Drawing, Line, Polygon, Rect, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
INK = colors.HexColor("#183b49")
PALE = colors.HexColor("#edf3f5")
RED = colors.HexColor("#ad3737")


def box(d, x, y, w, h, title, lines=()):
    d.add(Rect(x, y, w, h, rx=5, ry=5, fillColor=PALE, strokeColor=INK, strokeWidth=1))
    d.add(String(x+9, y+h-18, title, fontName="Helvetica-Bold", fontSize=10, fillColor=INK))
    for i, text in enumerate(lines):
        d.add(String(x+9, y+h-35-i*13, text, fontName="Helvetica", fontSize=8.5, fillColor=colors.black))


def arrow(d, x1, y1, x2, y2, label=None, lx=None, ly=None):
    from math import atan2, cos, sin
    d.add(Line(x1,y1,x2,y2,strokeColor=INK,strokeWidth=1.1))
    angle = atan2(y2-y1,x2-x1)
    d.add(Polygon([x2,y2,x2-6*cos(angle-.4),y2-6*sin(angle-.4),x2-6*cos(angle+.4),y2-6*sin(angle+.4)], fillColor=INK, strokeColor=INK))
    if label:
        d.add(String(lx if lx is not None else (x1+x2)/2, ly if ly is not None else (y1+y2)/2+5,
                     label, fontName="Helvetica", fontSize=8, fillColor=INK))


def boundary(d, x, y, w, h, label):
    d.add(Rect(x,y,w,h,fillColor=None,strokeColor=RED,strokeWidth=1.4,strokeDashArray=[5,3]))
    d.add(String(x+8,y+h-14,label,fontName="Helvetica-Bold",fontSize=9,fillColor=RED))



def architecture():
    d = Drawing(504, 130)
    box(d, 0, 42, 110, 65, "Browser", ["Login and room list", "HTML / CSS"])
    box(d, 177, 28, 150, 92, "Flask backend", ["Routes / Flask-Login", "Password and role checks", "Python sqlite3"])
    box(d, 394, 42, 110, 65, "SQLite", ["week6.db", "Four tables"])
    arrow(d, 110, 74, 177, 74, "HTTP", lx=126, ly=82)
    arrow(d, 327, 74, 394, 74, "Queries", lx=339, ly=82)
    d.add(String(0, 7, "Browser requests return server-rendered HTML. Local demonstration: 127.0.0.1.", fontSize=9))
    return d


def erd():
    d = Drawing(504, 245)
    box(d, 0, 130, 208, 110, "Users", [
        "PK id", "username (unique)", "password_hash", "role: guest / employee / admin"])
    box(d, 296, 130, 208, 110, "AuditLogs", [
        "PK id", "FK user_id -> Users.id (optional)", "action", "timestamp (UTC)"])
    arrow(d, 208, 177, 296, 177, "1 : 0..N", lx=228, ly=185)
    box(d, 0, 6, 208, 95, "Persons", [
        "PK id", "name", "kind: guest / employee"])
    box(d, 296, 6, 208, 95, "Rooms", [
        "PK id", "name (unique)", "capacity (positive integer)"])
    return d


def dfd():
    d = Drawing(504, 352)
    box(d, 154, 285, 200, 60, "E1 Browser", ["Guest / Employee / Administrator"])
    boundary(d, 4, 135, 496, 132, "TB1 - Untrusted browser to Flask")
    box(d, 18, 154, 216, 76, "P1 Login / logout", [
        "Input + CSRF checks", "Hash check and signed session"])
    box(d, 270, 154, 216, 76, "P2 Protected pages", [
        "Login + administrator role checks", "Read room reference data"])
    arrow(d, 211, 285, 125, 230, "F1 requests", lx=95, ly=273)
    arrow(d, 370, 230, 300, 285, "F2 HTML", lx=345, ly=275)
    arrow(d, 234, 190, 270, 190)
    boundary(d, 4, 8, 496, 112, "")
    d.add(String(130, 106, "TB2 - Flask to SQLite", fontName="Helvetica-Bold", fontSize=9, fillColor=RED))
    box(d, 18, 21, 320, 64, "SQLite data stores", [
        "D1 Users | D2 AuditLogs", "D3 Persons | D4 Rooms"])
    box(d, 354, 21, 132, 64, "P3 Local setup", ["init-db and seed", "Trusted CLI"])
    arrow(d, 99, 154, 99, 85, "F3", lx=109, ly=126)
    arrow(d, 81, 85, 81, 154)
    arrow(d, 292, 154, 292, 85, "F4", lx=302, ly=126)
    arrow(d, 275, 85, 275, 154)
    arrow(d, 354, 47, 338, 47)
    d.add(String(339, 94, "F5 initialization / seed", fontSize=8, fillColor=INK))
    return d

DIAGRAMS = {"architecture":architecture, "dfd":dfd, "erd":erd}
styles = getSampleStyleSheet()
styles.add(ParagraphStyle("BodyCustom",fontName="Helvetica",fontSize=9.3,leading=12.3,spaceAfter=7))
styles.add(ParagraphStyle("TableCustom",fontName="Helvetica",fontSize=8.1,leading=10.4,spaceAfter=0))
styles.add(ParagraphStyle("TitleCustom",fontName="Helvetica-Bold",fontSize=25,leading=30,textColor=colors.black,spaceBefore=25,spaceAfter=18))
styles.add(ParagraphStyle("HeadingCustom",fontName="Helvetica-Bold",fontSize=17,leading=22,textColor=INK,spaceAfter=12,keepWithNext=True))
styles.add(ParagraphStyle("SubCustom",fontName="Helvetica-Bold",fontSize=11,leading=15,textColor=INK,spaceBefore=8,spaceAfter=6,keepWithNext=True))


def paragraph(text, style="BodyCustom"):
    text=escape(text)
    text=re.sub(r"\*\*(.*?)\*\*",r"<b>\1</b>",text)
    return Paragraph(text,styles[style])


def table(rows):
    count=len(rows[0])
    if count == 2:
        widths=[59,445] if rows[0][0]=="ID" else [150,354]
    elif count == 3:
        widths=[58,318,128] if rows[0][0]=="ID" else [111,205,188]
    elif count == 4:
        widths=[109,83,40,272]
    else:
        widths=[504/count]*count
    data=[[paragraph(cell,"TableCustom") for cell in row] for row in rows]
    t=Table(data,colWidths=widths,repeatRows=1,hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),PALE), ("VALIGN",(0,0),(-1,-1),"TOP"),
        ("LINEBELOW",(0,0),(-1,0),.8,INK), ("LINEBELOW",(0,1),(-1,-1),.3,colors.HexColor("#c7d2d8")),
        ("LEFTPADDING",(0,0),(-1,-1),6),("RIGHTPADDING",(0,0),(-1,-1),6),
        ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
    ]))
    return t


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica",8)
    canvas.setFillColor(INK)
    canvas.drawString(54,28,"BIBIFI Group 11 | Secure Art Gallery | Fall 2026")
    canvas.drawRightString(558,28,str(doc.page))
    canvas.restoreState()


def build(stem):
    lines=(DOCS/f"{stem}.md").read_text(encoding="utf-8").splitlines()
    story=[];i=0
    while i<len(lines):
        line=lines[i].strip();i+=1
        if not line: continue
        if line=="---PAGE---": story.append(PageBreak());continue
        if line.startswith("[[diagram:"):
            name=line[len("[[diagram:"):-2]
            story.extend([DIAGRAMS[name](),Spacer(1,9)]);continue
        if line.startswith("|"):
            rows=[[cell.strip() for cell in line.strip("|").split("|")]]
            while i<len(lines) and lines[i].strip().startswith("|"):
                cells=[cell.strip() for cell in lines[i].strip().strip("|").split("|")]
                i+=1
                if all(re.fullmatch(r"[-: ]+",cell) for cell in cells):continue
                rows.append(cells)
            story.extend([table(rows),Spacer(1,8)]);continue
        if line.startswith("### "):story.append(paragraph(line[4:],"SubCustom"))
        elif line.startswith("## "):story.append(paragraph(line[3:],"HeadingCustom"))
        elif line.startswith("# "):story.append(paragraph(line[2:],"TitleCustom"))
        else:story.append(paragraph(line))
    doc=SimpleDocTemplate(str(DOCS/f"{stem}.pdf"),pagesize=letter,leftMargin=54,rightMargin=54,
                          topMargin=44,bottomMargin=46,title=stem.replace("_"," ").title(),
                          author="Huseyin Simsek and Gustavo Pepe",pageCompression=1)
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    print(f"Built docs/{stem}.pdf")


if __name__=="__main__":
    (DOCS/"diagrams").mkdir(exist_ok=True)
    for name,factory in DIAGRAMS.items():
        renderSVG.drawToFile(factory(),str(DOCS/"diagrams"/f"{name}.svg"))
    for stem in ("phase1_requirements","design_document"):
        build(stem)
