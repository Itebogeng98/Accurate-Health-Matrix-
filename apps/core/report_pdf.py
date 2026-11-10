"""Generate a branded, paginated PDF for one saved screening result."""
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

from django.conf import settings
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

from .forms import StrokePredictionForm, LungCancerPredictionForm

ACADEMIC_DISCLAIMER = 'Use results for learning and wellness support, not medical diagnosis.'


def report_inputs(record):
    form = StrokePredictionForm() if record.disease == 'stroke' else LungCancerPredictionForm()
    result = []
    for name, field in form.fields.items():
        if name not in record.input_data:
            continue
        value = record.input_data[name]
        if hasattr(field, 'choices'):
            value = next((label for key, label in field.choices if str(key) == str(value)), value)
        result.append((field.label or name.replace('_', ' ').capitalize(), value))
    return result


def build_screening_pdf(record):
    buffer = BytesIO()
    navy, teal = colors.HexColor('#10334b'), colors.HexColor('#007f82')
    font = 'Helvetica'
    bold = 'Helvetica-Bold'
    # Use a Unicode font when available on either supported deployment platform.
    for normal_path, bold_path in [
        (Path('C:/Windows/Fonts/arial.ttf'), Path('C:/Windows/Fonts/arialbd.ttf')),
        (Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'), Path('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf')),
    ]:
        if normal_path.exists() and bold_path.exists():
            if 'AHMRegular' not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont('AHMRegular', str(normal_path)))
                pdfmetrics.registerFont(TTFont('AHMBold', str(bold_path)))
            font, bold = 'AHMRegular', 'AHMBold'
            break
    styles = getSampleStyleSheet()
    for name in ('Normal', 'BodyText', 'Heading1', 'Heading2'):
        styles[name].fontName = bold if name.startswith('Heading') else font
        styles[name].textColor = navy
    styles['BodyText'].leading = 15
    styles['BodyText'].spaceAfter = 8
    styles['Heading1'].fontSize = 22
    styles['Heading1'].leading = 28
    styles['Heading2'].fontSize = 13
    styles['Heading2'].leading = 18
    styles.add(ParagraphStyle('SmallAHM', fontName=font, fontSize=9, leading=13, textColor=navy))
    styles.add(ParagraphStyle('NoticeAHM', fontName=bold, fontSize=10, leading=15, textColor=teal))
    def para(value, style='BodyText'):
        return Paragraph(escape(str(value)).replace('\n', '<br/>'), styles[style])
    generated_at = timezone.localtime()
    logo = Path(settings.BASE_DIR) / 'static/images/Accurate HealthMatrix pulse heart logo.png'
    def decorate(canvas, doc):
        canvas.saveState()
        width, height = doc.pagesize
        canvas.drawImage(ImageReader(str(logo)), 18*mm, height-33*mm,
                         width=67*mm, height=22.33*mm, preserveAspectRatio=True, mask='auto')
        canvas.setStrokeColor(teal)
        canvas.line(18*mm, height-37*mm, width-18*mm, height-37*mm)
        canvas.setFont(font, 7.5)
        canvas.setFillColor(navy)
        canvas.drawString(18*mm, 15*mm, 'Academic Website | ' + ACADEMIC_DISCLAIMER)
        canvas.drawString(18*mm, 10*mm, f'AHM screening report #{record.pk} | Educational model output')
        canvas.drawRightString(width-18*mm, 10*mm, f'Page {doc.page}')
        canvas.restoreState()
    doc = SimpleDocTemplate(buffer, pagesize=(210*mm,297*mm), leftMargin=18*mm,
        rightMargin=18*mm, topMargin=43*mm, bottomMargin=24*mm,
        title=f'AHM screening report #{record.pk}', author='Accurate HealthMatrix')
    story = [para(record.get_disease_display() + ' screening report', 'Heading1'),
        para(f'Report #{record.pk} | Screening: {timezone.localtime(record.created_at):%d %b %Y %H:%M %Z}', 'SmallAHM'),
        para(f'Generated: {generated_at:%d %b %Y %H:%M %Z}', 'SmallAHM'), Spacer(1,5*mm),
        para('Academic Website', 'NoticeAHM'), para(ACADEMIC_DISCLAIMER),
        para(f'Patient: {(' '.join(filter(None, [record.user.first_name, record.user.last_name])) or record.user.email)}'),
        para(f'Email: {record.user.email}'),
        para(f'Risk level: {record.risk_level}'),
        para(f'Model score: {record.probability_percent:.2f}%'),
        para('Saved guidance', 'Heading2'),
        para(record.recommendation or 'No guidance saved for this check.'),
        para('Information used', 'Heading2')]
    rows = [[para('Health indicator', 'NoticeAHM'), para('Saved value', 'NoticeAHM')]]
    rows += [[para(label, 'SmallAHM'), para(value, 'SmallAHM')] for label,value in report_inputs(record)]
    if len(rows) > 1:
        table = Table(rows, colWidths=[87*mm,87*mm], repeatRows=1, hAlign='LEFT')
        table.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#eaf4f3')),
            ('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),8),
            ('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),7),
            ('BOTTOMPADDING',(0,0),(-1,-1),7),
            ('LINEBELOW',(0,0),(-1,-1),.4,colors.HexColor('#d4e3e5')),
        ]))
        story.append(table)
    else:
        story.append(para('No inputs were saved for this check.'))
    story += [Spacer(1,5*mm), para('Important disclaimer', 'Heading2'),
        para('Model scores are not clinically validated probabilities or a medical diagnosis. '
             'Discuss health concerns with a qualified healthcare professional. '
             'An appointment request is not a confirmed booking.', 'SmallAHM')]
    doc.build(story, onFirstPage=decorate, onLaterPages=decorate)
    return buffer.getvalue()
