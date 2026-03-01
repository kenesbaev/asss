import io
import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# --- НАСТРОЙКА ШРИФТОВ ---
# ReportLab по умолчанию не поддерживает кириллицу.
# Нам нужно зарегистрировать шрифт, который её поддерживает (например, DejaVuSans или Arial).
# Пытаемся найти шрифт в системе или в папке проекта.

DEFAULT_FONT = 'Helvetica'
BOLD_FONT = 'Helvetica-Bold'

def register_fonts():
    global DEFAULT_FONT, BOLD_FONT
    
    # Список путей, где может лежать шрифт (можно добавить свой путь)
    possible_paths = [
        'static/fonts/DejaVuSans.ttf',
        'static/fonts/arial.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/TTF/DejaVuSans.ttf',
        'C:\\Windows\\Fonts\\arial.ttf'
    ]
    
    font_path = None
    for path in possible_paths:
        if os.path.exists(path):
            font_path = path
            break
            
    if font_path:
        try:
            pdfmetrics.registerFont(TTFont('RusFont', font_path))
            DEFAULT_FONT = 'RusFont'
            BOLD_FONT = 'RusFont' # Если есть Bold версия, можно загрузить отдельно, пока используем Regular
            print(f"Успешно загружен шрифт для кириллицы: {font_path}")
        except Exception as e:
            print(f"Ошибка загрузки шрифта {font_path}: {e}")
    else:
        print("ВНИМАНИЕ: Шрифт с поддержкой кириллицы не найден. Русский текст может не отображаться.")

# Вызываем регистрацию при импорте модуля
register_fonts()

def generate_academic_report_pdf(student_data, subjects_data):
    """
    Генерация детального академического отчета для студента.
    Сгруппировано по предметам, с отображением рейтинга, среднего балла и таблицы заданий.
    """
    try:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=1.5*cm, leftMargin=1.5*cm, topMargin=1.5*cm, bottomMargin=1.5*cm)
        
        story = []
        styles = getSampleStyleSheet()
        
        # Стили
        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            fontName=BOLD_FONT,
            fontSize=22,
            spaceAfter=10,
            textColor=colors.HexColor('#4318FF'),
            alignment=1 # Center
        )
        
        subtitle_style = ParagraphStyle(
            'SubtitleStyle',
            parent=styles['Normal'],
            fontName=DEFAULT_FONT,
            fontSize=10,
            textColor=colors.grey,
            alignment=1,
            spaceAfter=25
        )
        
        subject_title_style = ParagraphStyle(
            'SubjectTitle',
            parent=styles['Heading2'],
            fontName=BOLD_FONT,
            fontSize=16,
            spaceBefore=20,
            spaceAfter=10,
            textColor=colors.HexColor('#2B3674')
        )
        
        metric_style = ParagraphStyle(
            'MetricStyle',
            parent=styles['Normal'],
            fontName=DEFAULT_FONT,
            fontSize=11,
            leading=16,
            spaceAfter=4
        )
        
        table_header_style = ParagraphStyle(
            'TableHeader',
            parent=styles['Normal'],
            fontName=BOLD_FONT,
            fontSize=10,
            textColor=colors.white
        )
        
        normal_style = ParagraphStyle(
            'NormalStyle',
            parent=styles['Normal'],
            fontName=DEFAULT_FONT,
            fontSize=10,
            leading=12
        )
        
        # Заголовок отчета
        story.append(Paragraph(f"АКАДЕМИЧЕСКИЙ ОТЧЕТ", title_style))
        story.append(Paragraph(f"Студент: {student_data.get('name', 'N/A')} | Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}", subtitle_style))
        
        if not subjects_data:
            story.append(Paragraph("Нет данных по предметам.", normal_style))
        
        for subj in subjects_data:
            # Название предмета
            story.append(Paragraph(f"Название предмета: {subj['name']}", subject_title_style))
            
            # Рейтинг в звездах
            rating_val = subj.get('rating', 0)
            stars = "★" * int(rating_val) + "☆" * (5 - int(rating_val))
            
            # Метрики
            gpa = round(subj.get('average_score', 0) / 20, 2)
            avg_percent = round(subj.get('average_score', 0), 1)
            
            story.append(Paragraph(f"<b>Рейтинг:</b> {stars}", metric_style))
            story.append(Paragraph(f"<b>Средний балл:</b> {gpa}", metric_style))
            story.append(Paragraph(f"<b>Всего заданий:</b> {subj.get('total_assignments', 0)}", metric_style))
            story.append(Paragraph(f"<b>Выполнено:</b> {subj.get('completed_assignments', 0)}", metric_style))
            story.append(Paragraph(f"<b>Средний результат:</b> {avg_percent}%", metric_style))
            
            story.append(Spacer(1, 10))
            
            # Таблица заданий по этому предмету
            if subj.get('submissions'):
                table_data = [
                    [Paragraph("Название задания", table_header_style), 
                     Paragraph("Дата сдачи", table_header_style), 
                     Paragraph("Результат", table_header_style)]
                ]
                
                for s in subj['submissions']:
                    date_str = s['submitted_at'].strftime('%d.%m.%Y') if isinstance(s['submitted_at'], datetime) else str(s['submitted_at'])
                    score = s.get('score', 0)
                    table_data.append([
                        Paragraph(s.get('title', 'Unknown'), normal_style),
                        date_str,
                        f"{score}%"
                    ])
                
                t = Table(table_data, colWidths=[10*cm, 4*cm, 4*cm])
                t.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (-1, -1), DEFAULT_FONT),
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4318FF')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F4F7FE')]),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                    ('TOPPADDING', (0, 0), (-1, -1), 8),
                ]))
                story.append(t)
            else:
                story.append(Paragraph("Нет сданных заданий по этому предмету.", normal_style))
            
            story.append(Spacer(1, 20))
        
        # Футер
        story.append(Spacer(1, 40))
        story.append(Paragraph("Отчет сгенерирован автоматически платформой AI Assistant", 
                              ParagraphStyle('Footer', parent=normal_style, fontSize=8, textColor=colors.grey, alignment=1)))
        
        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        return pdf_bytes

    except Exception as e:
        print(f"Ошибка генерации Academic Report: {e}")
        import traceback
        traceback.print_exc()
        return generate_error_pdf(str(e))

    except Exception as e:
        print(f"Ошибка генерации Academic Report: {e}")
        return generate_error_pdf(str(e))

def generate_submission_pdf(submission_id, submission_data):
    """
    Генерация PDF отчета для конкретного задания (существующая функция, обновленная под шрифты)
    """
    try:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
        
        story = []
        styles = getSampleStyleSheet()
        
        # Стили с поддержкой кириллицы
        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            fontName=BOLD_FONT,
            fontSize=20,
            spaceAfter=20,
            textColor=colors.HexColor('#4318FF'),
            alignment=1
        )
        
        heading_style = ParagraphStyle(
            'HeadingStyle',
            parent=styles['Heading2'],
            fontName=BOLD_FONT,
            fontSize=14,
            spaceAfter=10,
            spaceBefore=15,
            textColor=colors.HexColor('#333333')
        )
        
        normal_style = ParagraphStyle(
            'NormalStyle',
            parent=styles['Normal'],
            fontName=DEFAULT_FONT,
            fontSize=10,
            spaceAfter=6
        )
        
        # Заголовок
        story.append(Paragraph("ОТЧЕТ ПО ПРОВЕРКЕ РАБОТЫ", title_style))
        story.append(Spacer(1, 15))
        
        # Основная информация
        story.append(Paragraph("Основная информация", heading_style))
        
        # Подготовка данных с защитой от None и кодировкой
        title = submission_data.get('assignment_title', 'Н/Д')
        student = submission_data.get('student_name', 'Н/Д')
        status = submission_data.get('status', 'Н/Д')
        
        info_data = [
            ["Задание:", Paragraph(title, normal_style)],
            ["Студент:", Paragraph(student, normal_style)],
            ["Дата сдачи:", submission_data.get('submitted_at', 'Н/Д')],
            ["Общий балл:", f"{submission_data.get('overall_score', 0)}/100"],
            ["Статус:", status]
        ]
        
        info_table = Table(info_data, colWidths=[3*cm, 12*cm])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), DEFAULT_FONT),
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F4F0FF')),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#4318FF')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        story.append(info_table)
        story.append(Spacer(1, 20))
        
        # Комментарий AI
        ai_comment = submission_data.get('ai_comment', '')
        if ai_comment:
            story.append(Paragraph("Комментарий AI", heading_style))
            story.append(Paragraph(ai_comment, normal_style))
            story.append(Spacer(1, 15))
        
        # Таблица с оценками по критериям
        story.append(Paragraph("Оценивание по пунктам", heading_style))
        
        criteria_data = [["№", "Критерий", "Балл", "Комментарий"]]
        
        criteria_list = submission_data.get('criteria_scores', [])
        
        for idx, criteria in enumerate(criteria_list, 1):
            criterion_name = criteria.get('criterion', f'Критерий {idx}')
            score = criteria.get('score', 0)
            comment = criteria.get('comment', '')
            
            score_color = colors.green if score >= 70 else colors.orange if score >= 50 else colors.red
            
            criteria_data.append([
                str(idx),
                Paragraph(criterion_name, normal_style),
                f'{score}',
                Paragraph(comment, normal_style)
            ])
        
        criteria_table = Table(criteria_data, colWidths=[1*cm, 5*cm, 2*cm, 8*cm])
        criteria_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), DEFAULT_FONT),
            ('FONTNAME', (0, 0), (-1, 0), BOLD_FONT),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4318FF')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FE')]),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        story.append(criteria_table)
        story.append(Spacer(1, 25))
        
        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        return pdf_bytes
        
    except Exception as e:
        print(f"Ошибка при генерации PDF (Submission): {str(e)}")
        import traceback
        traceback.print_exc()
        return generate_error_pdf(str(e))

def generate_error_pdf(error_message):
    """Генерация PDF с сообщением об ошибке (использует стандартный шрифт для гарантии)"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    story = []
    styles = getSampleStyleSheet()
    
    story.append(Paragraph("Error Generating Report / Ошибка генерации", styles['Heading1']))
    story.append(Spacer(1, 20))
    story.append(Paragraph("An error occurred while creating the PDF report:", styles['Normal']))
    story.append(Spacer(1, 10))
    
    # Пытаемся вывести ошибку, избегая проблем с кодировкой
    try:
        story.append(Paragraph(str(error_message), styles['Normal']))
    except:
        story.append(Paragraph("Unknown encoding error", styles['Normal']))
        
    story.append(Spacer(1, 20))
    story.append(Paragraph("Please ensure a Cyrillic font (e.g., DejaVuSans.ttf) is present in static/fonts/", styles['Normal']))
    
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return pdf_bytes