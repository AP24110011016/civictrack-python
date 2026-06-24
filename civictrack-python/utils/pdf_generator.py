"""
PDF Report Generator
Uses ReportLab to generate beautiful PDF reports for complaints and analytics
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.units import cm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                 TableStyle, HRFlowable, KeepTogether)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.graphics import renderPDF
import io
from datetime import datetime

# Color palette
GREEN      = HexColor('#1a6b3c')
GREEN_LIGHT= HexColor('#e8f5ee')
ACCENT     = HexColor('#f5a623')
RED        = HexColor('#e53e3e')
BLUE       = HexColor('#3b82f6')
DARK       = HexColor('#1a2e1a')
MUTED      = HexColor('#6b7f6b')
BORDER     = HexColor('#dce8dc')
BG         = HexColor('#f0f4f0')


def get_styles():
    styles = getSampleStyleSheet()
    custom = {
        'title': ParagraphStyle('title', fontSize=22, textColor=white, fontName='Helvetica-Bold', alignment=TA_CENTER, spaceAfter=4),
        'subtitle': ParagraphStyle('subtitle', fontSize=11, textColor=HexColor('#b8ddc8'), fontName='Helvetica', alignment=TA_CENTER),
        'h2': ParagraphStyle('h2', fontSize=14, textColor=GREEN, fontName='Helvetica-Bold', spaceBefore=16, spaceAfter=8),
        'h3': ParagraphStyle('h3', fontSize=11, textColor=DARK, fontName='Helvetica-Bold', spaceBefore=8, spaceAfter=4),
        'body': ParagraphStyle('body', fontSize=10, textColor=MUTED, fontName='Helvetica', spaceAfter=4, leading=14),
        'label': ParagraphStyle('label', fontSize=9, textColor=MUTED, fontName='Helvetica'),
        'value': ParagraphStyle('value', fontSize=10, textColor=DARK, fontName='Helvetica-Bold'),
        'center': ParagraphStyle('center', fontSize=10, textColor=MUTED, fontName='Helvetica', alignment=TA_CENTER),
        'small': ParagraphStyle('small', fontSize=8, textColor=MUTED, fontName='Helvetica'),
    }
    return custom


def status_color(status):
    colors = {
        'submitted':    '#ef4444',
        'acknowledged': '#3b82f6',
        'assigned':     '#8b5cf6',
        'in_progress':  '#f97316',
        'resolved':     '#22c55e',
        'rejected':     '#6b7280',
    }
    return HexColor(colors.get(status, '#6b7280'))


def priority_color(priority):
    colors = {'critical': '#ef4444', 'high': '#f97316', 'medium': '#eab308', 'low': '#22c55e'}
    return HexColor(colors.get(priority, '#6b7280'))


def generate_complaint_report(complaint, officer_name=None):
    """Generate a single complaint PDF report"""
    buf    = io.BytesIO()
    doc    = SimpleDocTemplate(buf, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    styles = get_styles()
    story  = []

    # ── Header ────────────────────────────────────────────────────────────────
    header_data = [[
        Paragraph('🏛️ CivicTrack', styles['title']),
        Paragraph('Complaint Intelligence Report', styles['subtitle']),
    ]]
    header_table = Table([[
        Paragraph('🏛️  CivicTrack', styles['title']),
    ]], colWidths=[17*cm])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), GREEN),
        ('ROUNDEDCORNERS', [8]),
        ('TOPPADDING', (0,0), (-1,-1), 16),
        ('BOTTOMPADDING', (0,0), (-1,-1), 16),
        ('LEFTPADDING', (0,0), (-1,-1), 20),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 0.3*cm))

    sub_table = Table([[Paragraph('Complaint Intelligence Report', styles['subtitle'])]], colWidths=[17*cm])
    sub_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), HexColor('#0d4a28')),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(sub_table)
    story.append(Spacer(1, 0.5*cm))

    # ── Tracking ID Banner ────────────────────────────────────────────────────
    tid   = complaint.get('trackingId', '—')
    status= complaint.get('status', 'submitted')
    tid_table = Table([[
        Paragraph(f'<b>Tracking ID:</b> {tid}', ParagraphStyle('tid', fontSize=12, textColor=GREEN, fontName='Helvetica-Bold')),
        Paragraph(f'Status: {status.upper().replace("_"," ")}', ParagraphStyle('st', fontSize=10, textColor=status_color(status), fontName='Helvetica-Bold', alignment=TA_RIGHT)),
    ]], colWidths=[10*cm, 7*cm])
    tid_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), GREEN_LIGHT),
        ('ROUNDEDCORNERS', [6]),
        ('TOPPADDING', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('LEFTPADDING', (0,0), (-1,-1), 14),
        ('RIGHTPADDING', (0,0), (-1,-1), 14),
        ('BOX', (0,0), (-1,-1), 1, BORDER),
    ]))
    story.append(tid_table)
    story.append(Spacer(1, 0.5*cm))

    # ── Complaint Details ──────────────────────────────────────────────────────
    story.append(Paragraph('Complaint Details', styles['h2']))

    details = [
        ['Title', complaint.get('title', '—')],
        ['Description', complaint.get('description', '—')],
        ['Issue Type', complaint.get('issueType', '—').replace('_', ' ').title()],
        ['Priority', complaint.get('priority', '—').upper()],
        ['Department', complaint.get('department', '—')],
        ['Location', complaint.get('location', {}).get('address', '—')],
        ['Ward', complaint.get('location', {}).get('ward', '—')],
        ['Submitted On', str(complaint.get('createdAt', '—'))[:10]],
        ['Assigned Officer', officer_name or 'Not yet assigned'],
    ]

    if complaint.get('resolvedAt'):
        details.append(['Resolved On', str(complaint.get('resolvedAt', ''))[:10]])
    if complaint.get('resolutionTimeHours'):
        details.append(['Resolution Time', f"{complaint.get('resolutionTimeHours')} hours"])

    det_data = [[
        Paragraph(k, styles['label']),
        Paragraph(str(v), styles['value'])
    ] for k, v in details]

    det_table = Table(det_data, colWidths=[4.5*cm, 12.5*cm])
    det_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,-1), BG),
        ('ROWBACKGROUNDS', (1,0), (1,-1), [white, HexColor('#f8faf8')]),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER),
        ('TOPPADDING', (0,0), (-1,-1), 7),
        ('BOTTOMPADDING', (0,0), (-1,-1), 7),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(det_table)
    story.append(Spacer(1, 0.5*cm))

    # ── AI Classification ─────────────────────────────────────────────────────
    ai = complaint.get('aiClassification', {})
    if ai:
        story.append(Paragraph('Python AI Classification', styles['h2']))
        ai_data = [
            [Paragraph('Predicted Type', styles['label']), Paragraph(str(ai.get('predictedType', '—')).replace('_',' ').title(), styles['value'])],
            [Paragraph('Confidence', styles['label']), Paragraph(f"{round(float(ai.get('confidence', 0))*100, 1)}%", styles['value'])],
        ]
        ai_table = Table(ai_data, colWidths=[4.5*cm, 12.5*cm])
        ai_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (0,-1), GREEN_LIGHT),
            ('GRID', (0,0), (-1,-1), 0.5, BORDER),
            ('TOPPADDING', (0,0), (-1,-1), 7),
            ('BOTTOMPADDING', (0,0), (-1,-1), 7),
            ('LEFTPADDING', (0,0), (-1,-1), 10),
        ]))
        story.append(ai_table)
        story.append(Spacer(1, 0.5*cm))

    # ── Timeline ───────────────────────────────────────────────────────────────
    timeline = complaint.get('timeline', [])
    if timeline:
        story.append(Paragraph('Resolution Timeline', styles['h2']))
        tl_data = [['Status', 'Message', 'Date']]
        for t in timeline:
            tl_data.append([
                t.get('status', '').replace('_', ' ').upper(),
                t.get('message', '—'),
                str(t.get('updatedAt', ''))[:10],
            ])
        tl_table = Table(tl_data, colWidths=[3.5*cm, 10*cm, 3.5*cm])
        tl_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), GREEN),
            ('TEXTCOLOR', (0,0), (-1,0), white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 9),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [white, HexColor('#f8faf8')]),
            ('GRID', (0,0), (-1,-1), 0.5, BORDER),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
            ('FONTSIZE', (0,1), (-1,-1), 9),
        ]))
        story.append(tl_table)

    # ── Footer ─────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 1*cm))
    story.append(HRFlowable(width='100%', color=BORDER))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(f'Generated by CivicTrack on {datetime.now().strftime("%d %B %Y at %I:%M %p")}', styles['center']))
    story.append(Paragraph('Bridging Citizens and Government through Technology', styles['center']))

    doc.build(story)
    buf.seek(0)
    return buf


def generate_analytics_report(stats, df=None):
    """Generate full analytics PDF report using ReportLab"""
    buf    = io.BytesIO()
    doc    = SimpleDocTemplate(buf, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    styles = get_styles()
    story  = []

    # ── Header ─────────────────────────────────────────────────────────────────
    hdr = Table([[Paragraph('🏛️  CivicTrack — Analytics Report', styles['title'])]], colWidths=[17*cm])
    hdr.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), GREEN),
        ('TOPPADDING', (0,0), (-1,-1), 18),
        ('BOTTOMPADDING', (0,0), (-1,-1), 18),
        ('LEFTPADDING', (0,0), (-1,-1), 20),
    ]))
    story.append(hdr)

    date_tbl = Table([[Paragraph(f'Generated: {datetime.now().strftime("%d %B %Y")}', styles['subtitle'])]], colWidths=[17*cm])
    date_tbl.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), HexColor('#0d4a28')), ('TOPPADDING', (0,0), (-1,-1), 6), ('BOTTOMPADDING', (0,0), (-1,-1), 6)]))
    story.append(date_tbl)
    story.append(Spacer(1, 0.6*cm))

    # ── Overview Stats ─────────────────────────────────────────────────────────
    story.append(Paragraph('Overview Statistics', styles['h2']))

    stat_items = [
        ('Total Complaints', stats.get('total', 0), GREEN),
        ('In Progress', stats.get('in_progress', 0), ACCENT),
        ('Resolved', stats.get('resolved', 0), HexColor('#22c55e')),
        ('Resolution Rate', f"{stats.get('resolution_rate', 0)}%", BLUE),
    ]

    stat_data = [[
        Table([[
            Paragraph(str(val), ParagraphStyle('sn', fontSize=22, textColor=color, fontName='Helvetica-Bold', alignment=TA_CENTER)),
            Paragraph(label, ParagraphStyle('sl', fontSize=9, textColor=MUTED, fontName='Helvetica', alignment=TA_CENTER)),
        ]], colWidths=[3.8*cm])
        for label, val, color in stat_items
    ]]

    stat_table = Table(stat_data, colWidths=[4.25*cm]*4)
    stat_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), white),
        ('BOX', (0,0), (0,-1), 1, BORDER),
        ('BOX', (1,0), (1,-1), 1, BORDER),
        ('BOX', (2,0), (2,-1), 1, BORDER),
        ('BOX', (3,0), (3,-1), 1, BORDER),
        ('TOPPADDING', (0,0), (-1,-1), 12),
        ('BOTTOMPADDING', (0,0), (-1,-1), 12),
    ]))
    story.append(stat_table)
    story.append(Spacer(1, 0.5*cm))

    # ── By Type Table ──────────────────────────────────────────────────────────
    by_type = stats.get('by_type', [])
    if by_type:
        story.append(Paragraph('Complaints by Issue Type', styles['h2']))
        type_data = [['Issue Type', 'Count']]
        for item in by_type:
            type_data.append([
                item.get('issue_type', item.get('_id', '—')).replace('_',' ').title(),
                str(item.get('count', 0))
            ])
        type_table = Table(type_data, colWidths=[13*cm, 4*cm])
        type_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), GREEN),
            ('TEXTCOLOR', (0,0), (-1,0), white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [white, GREEN_LIGHT]),
            ('GRID', (0,0), (-1,-1), 0.5, BORDER),
            ('TOPPADDING', (0,0), (-1,-1), 7),
            ('BOTTOMPADDING', (0,0), (-1,-1), 7),
            ('LEFTPADDING', (0,0), (-1,-1), 12),
            ('ALIGN', (1,0), (1,-1), 'CENTER'),
        ]))
        story.append(type_table)
        story.append(Spacer(1, 0.5*cm))

    # ── Department Performance ──────────────────────────────────────────────────
    dept_stats = stats.get('department_stats', [])
    if dept_stats:
        story.append(Paragraph('Department Performance', styles['h2']))
        dept_data = [['Department', 'Total', 'Resolved', 'Rate', 'Avg Time']]
        for d in dept_stats:
            dept_data.append([
                str(d.get('department', '—')),
                str(int(d.get('total', 0))),
                str(int(d.get('resolved', 0))),
                f"{d.get('resolution_rate', 0)}%",
                f"{d.get('avg_time', '—')}h" if d.get('avg_time') else '—',
            ])
        dept_table = Table(dept_data, colWidths=[7*cm, 2.2*cm, 2.2*cm, 2.8*cm, 2.8*cm])
        dept_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), GREEN),
            ('TEXTCOLOR', (0,0), (-1,0), white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [white, HexColor('#f8faf8')]),
            ('GRID', (0,0), (-1,-1), 0.5, BORDER),
            ('TOPPADDING', (0,0), (-1,-1), 7),
            ('BOTTOMPADDING', (0,0), (-1,-1), 7),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
            ('ALIGN', (1,0), (-1,-1), 'CENTER'),
            ('FONTSIZE', (0,0), (-1,-1), 9),
        ]))
        story.append(dept_table)

    # ── Footer ──────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 1*cm))
    story.append(HRFlowable(width='100%', color=BORDER))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph('CivicTrack — Smart Civic Complaint Management System', styles['center']))
    story.append(Paragraph('Powered by Python | Flask | OpenCV | NumPy | Pandas | ReportLab', styles['center']))

    doc.build(story)
    buf.seek(0)
    return buf
