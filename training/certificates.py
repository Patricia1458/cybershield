import io

from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

# CyberShield brand palette (static/css/style.css :root)
COLOR_DARKEST = HexColor('#051F20')
COLOR_MID = HexColor('#235347')
COLOR_LIGHT = HexColor('#8EB69B')
COLOR_LIGHTEST = HexColor('#DAF1DE')


def render_certificate_pdf(certificate):
    """Render a one-page landscape PDF certificate of completion. Returns raw PDF bytes."""
    buffer = io.BytesIO()
    page_size = landscape(letter)
    page_width, page_height = page_size
    c = canvas.Canvas(buffer, pagesize=page_size)

    # Background + outer/inner border
    c.setFillColor(white)
    c.rect(0, 0, page_width, page_height, fill=1, stroke=0)

    margin = 0.5 * inch
    c.setStrokeColor(COLOR_MID)
    c.setLineWidth(4)
    c.rect(margin, margin, page_width - 2 * margin, page_height - 2 * margin, fill=0, stroke=1)

    inner_margin = margin + 0.15 * inch
    c.setStrokeColor(COLOR_LIGHT)
    c.setLineWidth(1)
    c.rect(inner_margin, inner_margin, page_width - 2 * inner_margin, page_height - 2 * inner_margin, fill=0, stroke=1)

    center_x = page_width / 2

    # Header
    c.setFillColor(COLOR_MID)
    c.setFont('Helvetica-Bold', 14)
    c.drawCentredString(center_x, page_height - 1.3 * inch, 'CYBERSHIELD SECURITY AWARENESS TRAINING')

    c.setFillColor(COLOR_DARKEST)
    c.setFont('Helvetica-Bold', 34)
    c.drawCentredString(center_x, page_height - 1.9 * inch, 'Certificate of Completion')

    # Body
    employee_name = certificate.user.get_full_name() or certificate.user.username

    c.setFillColor(COLOR_MID)
    c.setFont('Helvetica', 14)
    c.drawCentredString(center_x, page_height - 2.7 * inch, 'This certifies that')

    c.setFillColor(COLOR_DARKEST)
    c.setFont('Helvetica-Bold', 28)
    c.drawCentredString(center_x, page_height - 3.35 * inch, employee_name)

    c.setFillColor(COLOR_MID)
    c.setFont('Helvetica', 14)
    c.drawCentredString(center_x, page_height - 3.9 * inch, 'has successfully completed the training module')

    c.setFillColor(COLOR_DARKEST)
    c.setFont('Helvetica-Bold', 20)
    c.drawCentredString(center_x, page_height - 4.45 * inch, certificate.module.title)

    # Footer: issued date (left) and certificate ID (right)
    footer_y = margin + 0.6 * inch
    c.setStrokeColor(COLOR_LIGHT)
    c.setLineWidth(1)
    c.line(margin + 0.75 * inch, footer_y + 0.3 * inch, page_width - margin - 0.75 * inch, footer_y + 0.3 * inch)

    c.setFillColor(COLOR_MID)
    c.setFont('Helvetica', 10)
    c.drawString(margin + 0.75 * inch, footer_y, f"Issued: {certificate.issued_at.strftime('%B %d, %Y')}")
    c.drawRightString(page_width - margin - 0.75 * inch, footer_y, f'Certificate ID: {certificate.id}')

    c.showPage()
    c.save()
    return buffer.getvalue()
