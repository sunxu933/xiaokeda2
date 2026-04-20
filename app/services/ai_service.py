"""AI Service for interacting with OpenAI-compatible APIs."""
import json
import time
import base64
from pathlib import Path
from datetime import datetime
from flask import current_app
from openai import OpenAI

from app.extensions import db
from app.models.ai_log import AIInteraction
from app.models.settings import AppSetting
from app.helpers import compress_image, extract_json_from_text


class AIService:
    """Service for AI interactions with support for OpenAI-compatible APIs."""

    def __init__(self):
        """Initialize AI service with configuration from settings."""
        self.endpoint = None
        self.api_key = None
        self.model = None
        self.vision_model = None
        self._client = None
        self._settings_loaded = False

    def _load_settings(self):
        """Load settings from database. Called lazily to avoid app context issues."""
        if self._settings_loaded:
            return
        self.endpoint = AppSetting.get('ai_api_endpoint', 'https://api.openai.com/v1')
        self.api_key = AppSetting.get('ai_api_key', '')
        self.model = AppSetting.get('ai_model', 'gpt-4o')
        self.vision_model = AppSetting.get('ai_vision_model', 'gpt-4o')
        self._settings_loaded = True

    @property
    def client(self):
        """Get or create OpenAI client."""
        self._load_settings()
        if self._client is None:
            self._client = OpenAI(api_key=self.api_key, base_url=self.endpoint)
        return self._client

    def _is_minimax_endpoint(self):
        """Check if endpoint is MiniMax."""
        self._load_settings()
        return 'minimaxi.com' in self.endpoint or 'minimax.io' in self.endpoint

    def _log_interaction(self, interaction_type, prompt, response, model_used,
                        duration_ms, tokens_used=None, image_path=None,
                        student_id=None, subject=None, related_id=None):
        """Log AI interaction to database."""
        try:
            log = AIInteraction(
                student_id=student_id,
                interaction_type=interaction_type,
                subject=subject,
                prompt_text=prompt[:10000] if prompt else None,
                response_text=response[:10000] if response else None,
                image_path=image_path,
                model_used=model_used,
                tokens_used=tokens_used,
                duration_ms=duration_ms,
                related_id=related_id
            )
            db.session.add(log)
            db.session.commit()
        except Exception as e:
            current_app.logger.error(f"Failed to log AI interaction: {e}")
            db.session.rollback()

    def _call_text(self, prompt, temperature=0.7, model=None):
        """Call text completion API."""
        start_time = time.time()
        self._load_settings()
        model = model or self.model

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature
            )
            duration_ms = int((time.time() - start_time) * 1000)
            content = response.choices[0].message.content
            tokens = response.usage.total_tokens if hasattr(response, 'usage') else None
            return content, duration_ms, tokens
        except Exception as e:
            current_app.logger.error(f"AI text call failed: {e}")
            raise

    def _call_vision(self, prompt, image_data=None, image_path=None, temperature=0.3, model=None):
        """Call vision/multimodal API."""
        start_time = time.time()
        model = model or self.vision_model

        content = [{"type": "text", "text": prompt}]

        if image_data:
            content.insert(0, {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}
            })
        elif image_path:
            full_path = Path(current_app.root_path).parent / 'app' / 'static' / image_path
            if full_path.exists():
                with open(full_path, 'rb') as f:
                    image_data = base64.b64encode(f.read()).decode('utf-8')
                content.insert(0, {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}
                })

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": content}],
                temperature=temperature
            )
            duration_ms = int((time.time() - start_time) * 1000)
            result = response.choices[0].message.content
            tokens = response.usage.total_tokens if hasattr(response, 'usage') else None
            return result, duration_ms, tokens
        except Exception as e:
            current_app.logger.error(f"AI vision call failed: {e}")
            raise

    def _call_vlm(self, prompt, image_path=None, temperature=0.3):
        """Call MiniMax VLM endpoint."""
        self._load_settings()
        if not self._is_minimax_endpoint():
            return self._call_vision(prompt, image_path=image_path, temperature=temperature)

        start_time = time.time()
        full_path = Path(current_app.root_path).parent / 'app' / 'static' / image_path if image_path else None

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.vision_model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt}
                    ]
                }
            ]
        }

        if full_path and full_path.exists():
            with open(full_path, 'rb') as f:
                image_base64 = base64.b64encode(f.read()).decode('utf-8')
            payload["messages"][0]["content"].insert(0, {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}
            })

        import requests
        try:
            response = requests.post(
                f"{self.endpoint}/v1/coding_plan/vlm",
                headers=headers,
                json=payload,
                timeout=120
            )
            duration_ms = int((time.time() - start_time) * 1000)
            result = response.json()
            return result.get('choices', [{}])[0].get('message', {}).get('content', ''), duration_ms, None
        except Exception as e:
            current_app.logger.error(f"MiniMax VLM call failed: {e}")
            raise

    def analyze_photo(self, image_path, grade, student_id=None):
        """Analyze photo of homework/questions."""
        prompt = f"""请分析这张图片中的题目内容。

这张图片是{grade}年级学生的学习材料。

请以JSON格式返回，结构如下：
{{
    "questions": [
        {{
            "content": "题目内容",
            "answer": "正确答案",
            "question_type": "choice/fill_blank/calculation/essay",
            "knowledge_point": "知识点",
            "difficulty": "easy/medium/hard"
        }}
    ]
}}

如果没有识别到有效题目，返回空数组。
"""
        result, duration, tokens = self._call_vision(prompt, image_path=image_path, temperature=0.3)
        self._log_interaction('analyze_photo', prompt, result, self.vision_model,
                             duration, tokens, image_path, student_id)
        return extract_json_from_text(result) or {'questions': []}

    def recognize_homework(self, image_path, grade, student_id=None):
        """Recognize homework from photo."""
        prompt = f"""请分析这张家庭作业照片。

这张照片来自{grade}年级学生。

请首先判断科目（语文/数学/英语），然后提取所有题目。

以JSON格式返回：
{{
    "subject": "科目",
    "questions": [
        {{
            "question_number": 1,
            "content": "题目内容",
            "student_answer": "学生答案（如果有）",
            "correct_answer": "正确答案",
            "is_correct": true/false,
            "mistake_type": "calculation/concept/careless/unknown",
            "knowledge_point": "知识点"
        }}
    ]
}}
"""
        result, duration, tokens = self._call_vision(prompt, image_path=image_path, temperature=0.3)
        self._log_interaction('recognize_homework', prompt, result, self.vision_model,
                             duration, tokens, image_path, student_id)
        return extract_json_from_text(result)

    def explain_problem(self, question_text, correct_answer, grade, student_id=None, subject=None):
        """Generate explanation for a problem."""
        prompt = f"""你是一位耐心的小学{grade}年级{subject}老师。请为学生详细讲解这道题目。

题目：{question_text}
正确答案：{correct_answer}

请用友好、易懂的方式分步讲解，要求：
1. 温和鼓励的语气
2. 清晰的解题步骤
3. 解释为什么这是正确的解法
4. 如果是计算题，可以提供一些类似的技巧

直接返回讲解文本，不需要JSON格式。
"""
        result, duration, tokens = self._call_text(prompt, temperature=0.7)
        self._log_interaction('explain_problem', prompt, result, self.model,
                             duration, tokens, student_id=student_id, subject=subject)
        return result

    def analyze_mistake(self, question_text, student_answer, correct_answer, student_id=None, subject=None):
        """Analyze a student's mistake."""
        prompt = f"""请分析这道错题：

题目：{question_text}
学生答案：{student_answer}
正确答案：{correct_answer}

请以JSON格式返回分析结果：
{{
    "error_type": "calculation/concept/careless/unknown",
    "root_cause": "错误根本原因分析",
    "weak_point": "学生薄弱知识点",
    "suggestion": "改进建议"
}}
"""
        result, duration, tokens = self._call_text(prompt, temperature=0.3)
        self._log_interaction('analyze_mistake', prompt, result, self.model,
                             duration, tokens, student_id=student_id, subject=subject)
        return extract_json_from_text(result)

    def generate_similar_problems(self, question_text, correct_answer, grade, count=3, subject=None):
        """Generate similar practice problems."""
        prompt = f"""请生成{count}道与下面这道题类似的练习题（{grade}年级{subject}）：

原题：{question_text}
正确答案：{correct_answer}

要求：
1. 难度相近
2. 题型相同或类似
3. 数字和具体内容有所变化

以JSON格式返回：
{{
    "problems": [
        {{
            "question": "新题目内容",
            "answer": "正确答案",
            "explanation": "简要解析",
            "difficulty": "easy/medium/hard",
            "knowledge_point": "知识点"
        }}
    ]
}}
"""
        result, duration, tokens = self._call_text(prompt, temperature=0.7)
        self._log_interaction('generate_similar_problems', prompt, result, self.model,
                             duration, tokens, student_id=None, subject=subject)
        return extract_json_from_text(result) or {'problems': []}

    def generate_practice_by_topic(self, topic, subject, grade, count=5):
        """Generate practice problems by topic."""
        prompt = f"""请为{grade}年级{subject}科目生成关于"{topic}"的练习题。

要求：
1. 混合题型（选择题、填空题、计算题等）
2. 难度适中
3. 贴近学校考试风格

以JSON格式返回：
{{
    "problems": [
        {{
            "type": "choice/fill_blank/calculation",
            "question": "题目内容",
            "options": ["A选项", "B选项", "C选项", "D选项"],  // 如果是选择题
            "answer": "正确答案",
            "explanation": "解析",
            "difficulty": "easy/medium/hard",
            "score": 5
        }}
    ]
}}
"""
        result, duration, tokens = self._call_text(prompt, temperature=0.7)
        self._log_interaction('generate_practice_by_topic', prompt, result, self.model,
                             duration, tokens, student_id=None, subject=subject)
        return extract_json_from_text(result) or {'problems': []}

    def generate_mock_test(self, topics, subject, grade, total_score=100):
        """Generate a mock test from topics."""
        topics_str = ', '.join(topics) if isinstance(topics, list) else topics
        prompt = f"""请为{grade}年级{subject}科目生成一套模拟试卷。

覆盖主题：{topics_str}

要求：
1. 难度分布：30%简单，50%中等，20%困难
2. 满分{total_score}分
3. 包含多种题型
4. 每道题标注分值

以JSON格式返回：
{{
    "title": "模拟测试标题",
    "questions": [
        {{
            "type": "choice/fill_blank/calculation/essay",
            "question": "题目内容",
            "options": [],  // 选择题选项
            "answer": "正确答案",
            "explanation": "解析",
            "knowledge_point": "知识点",
            "difficulty": "easy/medium/hard",
            "score": 分值
        }}
    ]
}}
"""
        result, duration, tokens = self._call_text(prompt, temperature=0.7)
        self._log_interaction('generate_mock_test', prompt, result, self.model,
                             duration, tokens, student_id=None, subject=subject)
        return extract_json_from_text(result)

    def generate_knowledge_summary(self, chapter, subject, grade):
        """Generate knowledge summary for a chapter."""
        prompt = f"""请为{grade}年级{subject}科目编写"{chapter}"章节的知识汇总。

要求：
1. 教学专家风格
2. 包含核心知识点
3. 提供记忆技巧
4. 适合小学生理解

直接返回文本，不需要JSON格式。
"""
        result, duration, tokens = self._call_text(prompt, temperature=0.7)
        self._log_interaction('generate_knowledge_summary', prompt, result, self.model,
                             duration, tokens, student_id=None, subject=subject)
        return result

    def analyze_material_image(self, image_path, grade, student_id=None):
        """Analyze learning material image."""
        prompt = f"""请分析这张学习资料图片（{grade}年级）。

请提取以下信息并以JSON格式返回：
{{
    "material_type": "试卷/练习册/讲义/课本/笔记/其他",
    "subject": "科目（语文/数学/英语）",
    "knowledge_points": [
        {{
            "chapter": "章节",
            "topic": "知识点主题",
            "content": "详细内容",
            "key_points": ["要点1", "要点2"],
            "difficulty": "easy/medium/hard",
            "importance": "core/important/supplementary"
        }}
    ],
    "questions": [
        {{
            "question_text": "题目内容",
            "answer": "正确答案",
            "explanation": "解析",
            "question_type": "choice/fill_blank/calculation/essay",
            "knowledge_point": "关联知识点",
            "difficulty": "easy/medium/hard",
            "score": 分值
        }}
    ]
}}
"""
        result, duration, tokens = self._call_vision(prompt, image_path=image_path, temperature=0.3)
        self._log_interaction('analyze_material_image', prompt, result, self.vision_model,
                             duration, tokens, image_path, student_id)
        return extract_json_from_text(result)

    def analyze_pdf_page(self, image_path, page_number, student_id=None):
        """Analyze a PDF page (2nd+ page)."""
        prompt = f"""请分析这张PDF第{page_number}页的内容。

这道题是否包含答案或解析内容？
- 如果是答案/解析页，请标注is_answer_page: true
- 如果是题目页，请提取题目和知识点

以JSON格式返回：
{{
    "is_answer_page": true/false,
    "questions": [],
    "knowledge_points": []
}}

如果标注为is_answer_page=true，其他字段可以为空。
"""
        result, duration, tokens = self._call_vision(prompt, image_path=image_path, temperature=0.3)
        self._log_interaction('analyze_pdf_page', prompt, result, self.vision_model,
                             duration, tokens, image_path, student_id)
        return extract_json_from_text(result) or {'is_answer_page': False, 'questions': [], 'knowledge_points': []}

    def analyze_text_content(self, text, grade, student_id=None):
        """Analyze text content from DOCX or extracted PDF text."""
        prompt = f"""请分析以下学习资料文本内容（{grade}年级）。

请以JSON格式提取：
{{
    "material_type": "试卷/练习册/讲义/课本/笔记/其他",
    "subject": "科目",
    "knowledge_points": [],
    "questions": []
}}

资料文本：
{text[:8000]}
"""
        result, duration, tokens = self._call_text(prompt, temperature=0.3)
        self._log_interaction('analyze_text_content', prompt, result, self.model,
                             duration, tokens, student_id=student_id)
        return extract_json_from_text(result)

    def extract_questions_from_text(self, text, student_id=None):
        """Extract questions from plain text."""
        prompt = f"""请从以下文本中提取所有题目。

以JSON数组格式返回：
[
    {{
        "question_text": "题目内容",
        "answer": "正确答案",
        "question_type": "choice/fill_blank/calculation/essay",
        "knowledge_point": "知识点"
    }}
]

如果文本中没有题目，返回空数组[]。

文本内容：
{text[:8000]}
"""
        result, duration, tokens = self._call_text(prompt, temperature=0.3)
        self._log_interaction('extract_questions_from_text', prompt, result, self.model,
                             duration, tokens, student_id=student_id)
        extracted = extract_json_from_text(result)
        return extracted if isinstance(extracted, list) else []

    def generate_questions_from_knowledge(self, knowledge_points, subject, grade, count=5):
        """Generate questions from knowledge points."""
        points_str = ', '.join(knowledge_points) if isinstance(knowledge_points, list) else knowledge_points
        prompt = f"""基于以下{grade}年级{subject}知识点生成练习题：

{points_str}

请生成{count}道练习题，以JSON格式：
{{
    "questions": [
        {{
            "question": "题目",
            "answer": "答案",
            "explanation": "解析",
            "type": "choice/fill_blank/calculation",
            "difficulty": "medium",
            "knowledge_point": "关联知识点"
        }}
    ]
}}
"""
        result, duration, tokens = self._call_text(prompt, temperature=0.7)
        self._log_interaction('generate_questions_from_knowledge', prompt, result, self.model,
                             duration, tokens, student_id=None, subject=subject)
        return extract_json_from_text(result) or {'questions': []}

    def chat(self, messages, grade, subject=None):
        """Chat with AI tutor."""
        system_prompt = f"""你是一位专业、耐心的小学{grade}年级学习辅导老师。
擅长用生动有趣的方式解释知识点。
可以用emoji辅助表达。
回答要简洁明了，适合小学生理解。"""

        formatted_messages = [{"role": "system", "content": system_prompt}]
        for msg in messages:
            formatted_messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", "")
            })

        start_time = time.time()
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=formatted_messages,
                temperature=0.7
            )
            duration_ms = int((time.time() - start_time) * 1000)
            result = response.choices[0].message.content
            tokens = response.usage.total_tokens if hasattr(response, 'usage') else None
            self._log_interaction('chat', str(messages), result, self.model,
                                 duration_ms, tokens, student_id=None, subject=subject)
            return result
        except Exception as e:
            current_app.logger.error(f"AI chat failed: {e}")
            raise

    def test_connection(self):
        """Test AI API connection."""
        prompt = "请回复'连接成功'。"
        try:
            result, duration, tokens = self._call_text(prompt, temperature=0.0)
            return {'success': True, 'message': '连接成功', 'response': result}
        except Exception as e:
            return {'success': False, 'message': str(e)}


# Global singleton instance - lazy initialization
_ai_service = None

def get_ai_service():
    """Get or create the AI service singleton. Must be called within app context."""
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService()
    return _ai_service

# For backwards compatibility - will be set properly after first request
class _LazyProxy:
    """Lazy proxy that initializes on first access."""
    def __getattr__(self, name):
        from flask import current_app
        if current_app:
            return getattr(get_ai_service(), name)
        raise RuntimeError("AI service not initialized")

ai_service = _LazyProxy()
