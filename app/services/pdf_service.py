"""PDF generation service for compiling practice sheets."""
import os
import re
import json
import uuid
from pathlib import Path
from datetime import datetime, timedelta
from io import BytesIO

from fpdf import FPDF


class CompilationPDF(FPDF):
    """Custom FPDF class with Chinese font support."""

    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)

    def header(self):
        pass

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', align='C')


class PDFService:
    """Service for generating PDF documents."""

    # Chinese fonts path (Windows)
    FONT_PATHS = [
        'C:/Windows/Fonts/msyh.ttc',  # Microsoft YaHei
        'C:/Windows/Fonts/simhei.ttf',  # SimHei
        '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',  # Linux
        '/System/Library/Fonts/PingFang.ttc',  # macOS
    ]

    @staticmethod
    def get_font_path():
        """Get available Chinese font path."""
        for path in PDFService.FONT_PATHS:
            if os.path.exists(path):
                return path
        return None

    @staticmethod
    def build(title, sections, include_answers=True):
        """Build a compiled PDF from questions.

        Args:
            title: PDF title
            sections: List of section dicts with material_title, material, questions
            include_answers: Whether to include answer section

        Returns:
            bytes: PDF content
        """
        pdf = CompilationPDF()
        font_path = PDFService.get_font_path()

        if font_path:
            pdf.add_font('Chinese', '', font_path, uni=True)
            pdf.set_font('Chinese', '', 10)
        else:
            pdf.set_font('Helvetica', '', 10)

        # Cover page
        pdf.add_page()
        pdf.set_font('Helvetica', 'B', 20)
        pdf.cell(0, 20, title, ln=True, align='C')
        pdf.ln(10)

        total_questions = sum(len(s.get('questions', [])) for s in sections)
        pdf.set_font('Helvetica', '', 12)
        pdf.cell(0, 10, f"总题数: {total_questions}", ln=True, align='C')
        pdf.cell(0, 10, f"来源试卷数: {len(sections)}", ln=True, align='C')
        pdf.cell(0, 10, f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align='C')

        # Question pages
        question_number = 1
        for section in sections:
            material_title = section.get('material_title', 'Unknown')
            questions = section.get('questions', [])

            if not questions:
                continue

            # Filter answer pages
            filtered_questions = PDFService._filter_answer_questions(questions)

            for q in filtered_questions:
                # Determine if need new page (essay questions get full page)
                q_type = q.get('question_type', 'other')
                if q_type == 'essay':
                    pdf.add_page()

                question_text = PDFService._clean_question_text(q.get('question_text', ''))
                pdf.set_font('Helvetica', 'B', 10)
                pdf.multi_cell(0, 6, f"{question_number}. {question_text}")
                pdf.ln(2)

                # Add options if present
                options = q.get('options', [])
                if options and isinstance(options, list):
                    for opt in options:
                        pdf.set_font('Helvetica', '', 9)
                        pdf.cell(10, 5, '', border=0)
                        pdf.multi_cell(0, 5, opt)

                pdf.ln(5)
                question_number += 1

        # Answer pages
        if include_answers:
            pdf.add_page()
            pdf.set_font('Helvetica', 'B', 16)
            pdf.cell(0, 15, '参考答案', ln=True, align='C')
            pdf.ln(5)

            q_num = 1
            for section in sections:
                questions = section.get('questions', [])
                filtered_questions = PDFService._filter_answer_questions(questions)

                for q in filtered_questions:
                    answer = q.get('answer', 'N/A')
                    explanation = q.get('explanation', '')

                    pdf.set_font('Helvetica', 'B', 10)
                    pdf.multi_cell(0, 6, f"{q_num}. 答案: {answer}")
                    pdf.ln(1)

                    if explanation:
                        pdf.set_font('Helvetica', 'I', 9)
                        pdf.set_text_color(100, 100, 100)
                        pdf.multi_cell(0, 5, f"解析: {explanation}")
                        pdf.set_text_color(0, 0, 0)

                    pdf.ln(4)
                    q_num += 1

        return bytes(pdf.output())

    @staticmethod
    def _filter_answer_questions(questions):
        """Filter out questions that are likely from answer section."""
        filtered = []
        for q in questions:
            text = q.get('question_text', '')
            if PDFService._is_likely_answer_section(text):
                continue
            filtered.append(q)
        return filtered

    @staticmethod
    def _is_likely_answer_section(text):
        """Check if text appears to be from an answer section.

        Uses multiple heuristics to reduce false positives:
        - Answer section headers at start of text
        - Short text with answer patterns (not questions)
        - Common answer section titles
        """
        if not text or len(text.strip()) < 2:
            return False

        text = text.strip()

        # Check for answer section titles at the start (strong indicators)
        answer_section_patterns = [
            r'^答案[：:]\s*\S',  # "答案：xxx" or "答案: xxx"
            r'^【答案】',
            r'^【解析】',
            r'^解题思路[：:]',
            r'^\d+[.、]\s*答案[：:]?\s*\S',  # "1. 答案：xxx"
        ]

        for pattern in answer_section_patterns:
            if re.match(pattern, text):
                return True

        # Check if text looks like an answer (short, no question mark)
        # and contains explicit answer markers
        has_answer_marker = any(k in text for k in ['答案：', '答案:', '【答案】', '【解析】'])
        is_short_text = len(text) < 100
        likely_question = '？' in text or '?' in text or '选择' in text

        if has_answer_marker and is_short_text and not likely_question:
            return True

        return False

    @staticmethod
    def _clean_question_text(text):
        """Clean question text for PDF output."""
        if not text:
            return ''

        # Remove score markers
        text = re.sub(r'\(\d+分\)', '', text)
        text = re.sub(r'\[\d+分\]', '', text)

        # Convert LaTeX
        text = text.replace('$\\square$', '□')
        text = text.replace('$\\Box$', '□')

        # Remove chapter headers
        chapter_patterns = [
            r'^一、.*',
            r'^二、.*',
            r'^三、.*',
            r'^四、.*',
            r'^五、.*',
            r'^选择题\s*',
            r'^填空题\s*',
            r'^计算题\s*',
            r'^解答题\s*',
        ]
        for pattern in chapter_patterns:
            text = re.sub(pattern, '', text)

        # Remove question references
        text = re.sub(r'（\d+、\d+题）', '', text)
        text = re.sub(r'\(\d+、\d+题\)', '', text)

        # Remove leading question numbers
        text = re.sub(r'^\d+[\.\、]\s*', '', text)

        return text.strip()

    @staticmethod
    def save_compiled_pdf(pdf_content, filename=None):
        """Save compiled PDF to uploads directory."""
        if not filename:
            filename = f"compiled_{uuid.uuid4().hex}.pdf"

        uploads_dir = Path(__file__).parent.parent / 'static' / 'uploads' / 'materials'
        uploads_dir.mkdir(parents=True, exist_ok=True)

        filepath = uploads_dir / filename
        with open(filepath, 'wb') as f:
            f.write(pdf_content)

        return f"uploads/materials/{filename}"

    @staticmethod
    def cleanup_old_pdfs(hours=1):
        """Clean up compiled PDFs older than specified hours."""
        uploads_dir = Path(__file__).parent.parent / 'static' / 'uploads' / 'materials'
        if not uploads_dir.exists():
            return

        cutoff = datetime.now() - timedelta(hours=hours)
        for pdf_file in uploads_dir.glob('compiled_*.pdf'):
            mtime = datetime.fromtimestamp(pdf_file.stat().st_mtime)
            if mtime < cutoff:
                pdf_file.unlink()


pdf_service = PDFService()
