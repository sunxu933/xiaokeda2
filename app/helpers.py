"""Utility functions."""
import os
import json
import re
import uuid
from datetime import datetime, date, timedelta
from pathlib import Path
from flask import g
from PIL import Image


def allowed_file(filename, allowed_extensions):
    """Check if file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions


def save_uploaded_file(file, subfolder):
    """Save uploaded file and return the relative path."""
    from app import create_upload_dir
    create_upload_dir()

    ext = file.filename.rsplit('.', 1)[1].lower()
    unique_filename = f"{uuid.uuid4().hex}.{ext}"
    relative_path = f"uploads/{subfolder}/{unique_filename}"
    full_path = Path(__file__).parent.parent / 'app' / 'static' / relative_path

    file.save(str(full_path))
    return relative_path


def compress_image(image_path, max_size=1568, quality=85):
    """Compress image for AI processing."""
    img = Image.open(image_path)
    if img.mode == 'RGBA':
        img = img.convert('RGB')

    width, height = img.size
    if max(width, height) > max_size:
        ratio = max_size / max(width, height)
        new_width = int(width * ratio)
        new_height = int(height * ratio)
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

    img.save(image_path, 'JPEG', quality=quality)
    return image_path


def extract_json_from_text(text):
    """Extract JSON from AI response text."""
    if not text:
        return None

    text = text.strip()

    # Try direct JSON parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try markdown code block
    json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # Try to find JSON object/array with bracket matching
    for start_char, end_char in [('{', '}'), ('[', ']')]:
        start_idx = text.find(start_char)
        if start_idx != -1:
            depth = 0
            end_idx = start_idx
            for i, c in enumerate(text[start_idx:], start=start_idx):
                if c == start_char:
                    depth += 1
                elif c == end_char:
                    depth -= 1
                if depth == 0:
                    end_idx = i + 1
                    break
            if end_idx > start_idx:
                try:
                    return json.loads(text[start_idx:end_idx])
                except json.JSONDecodeError:
                    pass

    return None


def infer_subject_from_filename(filename):
    """Infer subject from filename."""
    filename_lower = filename.lower()
    if '数学' in filename or 'math' in filename_lower:
        return '数学'
    elif '语文' in filename or 'chinese' in filename_lower:
        return '语文'
    elif '英语' in filename or 'english' in filename_lower or '英语' in filename:
        return '英语'
    return None


def infer_grade_from_filename(filename):
    """Infer grade from filename."""
    patterns = [
        r'(\d)年级',
        r'三年級',  # Traditional
        r' grade (\d)',
        r'Grade (\d)',
    ]
    for pattern in patterns:
        match = re.search(pattern, filename)
        if match:
            return int(match.group(1))
    return None


def format_timedelta(delta):
    """Format timedelta to human readable string."""
    if isinstance(delta, timedelta):
        total_minutes = int(delta.total_seconds() / 60)
    else:
        total_minutes = delta

    hours = total_minutes // 60
    minutes = total_minutes % 60
    if hours > 0:
        return f"{hours}小时{minutes}分钟"
    return f"{minutes}分钟"


def calculate_spaced_review(review_count):
    """Calculate next review date based on spaced repetition."""
    INTERVALS = [1, 3, 7, 14, 30]
    idx = min(review_count, len(INTERVALS) - 1)
    return date.today() + timedelta(days=INTERVALS[idx])
