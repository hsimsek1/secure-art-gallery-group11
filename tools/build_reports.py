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
    d=Drawing(504,205)
    box(d,3,85,108,72,"Browser",["Guest / Employee", "Administrator"])
    boundary(d,131,48,241,145,"One Flask application")
    box(d,143,85,100,72,"Web interface",["HTML / CSS", "Jinja templates"])
    box(d,260,85,100,72,"Backend",["Routes / services", "Login / roles"])
    box(d,396,85,105,72,"SQLite",["SQLAlchemy", "Five tables"])
    arrow(d,111,121,143,121)
    arrow(d,243,121,260,121)
    arrow(d,360,121,396,121)
    d.add(String(4,29,"HTTP on loopback now; HTTPS planned for network deployment.",fontName="Helvetica",fontSize=9,fillColor=INK))
    d.add(String(4,13,"Responses return encoded HTML; data persists in instance/gallery.db.",fontName="Helvetica",fontSize=9,fillColor=INK))
    return d


def dfd():
    d=Drawing(504,395)
    box(d,143,331,210,54,"E1 User browser",["Guest / Employee / Administrator"])
    boundary(d,4,119,496,198,"TB1 Client to server trust boundary")
    box(d,143,236,210,53,"P1 Request checks",["Session / role / CSRF / validation"])
    arrow(d,218,331,218,289,"F1 inputs",lx=154,ly=319)
    arrow(d,292,289,292,331,"F2 HTML",lx=302,ly=322)
    box(d,17,142,135,63,"P2 Authentication",["Login / logout", "Verify hash and account"])
    box(d,184,142,135,63,"P3 Protected writes",["Events / persons / users", "Validate state + commit"])
    box(d,351,142,135,63,"P4 Authorized reads",["Occupancy / history", "Admin audit review"])
    arrow(d,168,236,85,205)
    arrow(d,250,236,250,205)
    arrow(d,330,236,416,205)
    boundary(d,4,6,496,102,"TB2 Application to persistence trust boundary")
    box(d,17,17,460,59,"SQLite relational stores",[
        "D1 Users | D2 Persons | D3 Rooms | D4 GalleryEvents | D5 AuditLogs",
        "Server-only file access; browsers cannot access these stores directly."])
    arrow(d,75,142,75,76,"F3",lx=87,ly=126)
    arrow(d,75,76,75,142)
    arrow(d,250,142,250,76,"F4",lx=260,ly=126)
    arrow(d,250,76,250,142)
    arrow(d,414,142,414,76,"F5",lx=425,ly=126)
    arrow(d,414,76,414,142)
    d.add(Line(353,263,493,263,strokeColor=INK))
    d.add(Line(493,263,493,43,strokeColor=INK))
    arrow(d,493,43,477,43)
    d.add(String(471,272,"F6",fontName="Helvetica",fontSize=8,fillColor=INK))
    return d


def erd():
    d=Drawing(504,452)
    box(d,4,280,207,165,"Users",["PK id : integer", "username : text UNIQUE", "password_hash : text", "role : guest / employee / admin", "active : boolean", "created_at : UTC datetime", "session_version : integer"])
    box(d,296,329,204,116,"Persons",["PK id : integer", "name : text", "kind : guest / employee", "created_at : UTC datetime"])
    box(d,296,212,204,95,"Rooms",["PK id : integer", "name : text UNIQUE", "capacity : positive integer"])
    box(d,4,10,220,190,"GalleryEvents",["PK id : integer", "FK person_id -> Persons.id", "FK room_id -> Rooms.id (optional)", "event_type : one of four types", "timestamp : UTC datetime", "FK created_by -> Users.id"])
    box(d,296,10,204,165,"AuditLogs",["PK id : integer", "FK user_id -> Users.id (optional)", "action : text", "details : bounded text", "timestamp : UTC datetime", "result : SUCCESS / REJECTED"])
    arrow(d,77,280,77,200,"1 to N",lx=85,ly=235)
    # Orthogonal connectors avoid crossing field text.
    d.add(Line(296,371,251,371,strokeColor=INK));d.add(Line(251,371,251,179,strokeColor=INK))
    arrow(d,251,179,224,179,"1 to N",lx=251,ly=183)
    d.add(Line(296,257,266,257,strokeColor=INK));d.add(Line(266,257,266,140,strokeColor=INK))
    arrow(d,266,140,224,140,"1 to N",lx=235,ly=125)
    d.add(Line(211,302,236,302,strokeColor=INK));d.add(Line(236,302,236,225,strokeColor=INK))
    d.add(Line(236,225,286,225,strokeColor=INK));d.add(Line(286,225,286,92,strokeColor=INK))
    arrow(d,286,92,296,92)
    d.add(String(295,187,"Users 1 to N AuditLogs",fontName="Helvetica",fontSize=8,fillColor=INK))
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
