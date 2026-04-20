"""WTForms for xiaokeda application."""
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, TextAreaField, IntegerField, FloatField, BooleanField, DateField
from wtforms.validators import DataRequired, Optional, Length, NumberRange


class StudentForm(FlaskForm):
    """Student profile form."""
    name = StringField('姓名', validators=[DataRequired(), Length(max=50)])
    grade = SelectField('年级', coerce=int, validators=[DataRequired()])
    school = StringField('学校', validators=[Optional(), Length(max=100)])


class HomeworkForm(FlaskForm):
    """Homework form."""
    title = StringField('作业标题', validators=[DataRequired(), Length(max=200)])
    subject = SelectField('科目', choices=[
        ('语文', '语文'), ('数学', '数学'), ('英语', '英语')
    ], validators=[DataRequired()])
    homework_date = DateField('作业日期', validators=[DataRequired()])
    due_date = DateField('截止日期', validators=[Optional()])
    notes = TextAreaField('备注', validators=[Optional()])


class HomeworkItemForm(FlaskForm):
    """Homework item form."""
    question_number = IntegerField('题号', validators=[Optional()])
    content = TextAreaField('题目内容', validators=[Optional()])
    student_answer = StringField('学生答案', validators=[Optional()])
    correct_answer = StringField('正确答案', validators=[Optional()])
    is_correct = SelectField('是否正确', choices=[
        ('', '未评分'), ('true', '正确'), ('false', '错误')
    ], validators=[Optional()])
    mistake_type = SelectField('错误类型', choices=[
        ('', '未选择'),
        ('calculation', '计算错误'),
        ('concept', '概念错误'),
        ('careless', '粗心错误'),
        ('unknown', '未知')
    ], validators=[Optional()])
    knowledge_point = StringField('知识点', validators=[Optional(), Length(max=100)])


class MistakeForm(FlaskForm):
    """Mistake form."""
    subject = SelectField('科目', choices=[
        ('语文', '语文'), ('数学', '数学'), ('英语', '英语')
    ], validators=[DataRequired()])
    topic = StringField('主题', validators=[Optional(), Length(max=100)])
    knowledge_point = StringField('知识点', validators=[Optional(), Length(max=100)])
    question_text = TextAreaField('题目内容', validators=[DataRequired()])
    student_answer = StringField('学生错误答案', validators=[Optional()])
    correct_answer = StringField('正确答案', validators=[Optional()])
    explanation = TextAreaField('解析', validators=[Optional()])
    difficulty = SelectField('难度', choices=[
        ('easy', '简单'), ('medium', '中等'), ('hard', '困难')
    ], validators=[Optional()])


class ReviewPlanForm(FlaskForm):
    """Review plan form."""
    title = StringField('计划名称', validators=[DataRequired(), Length(max=200)])
    subject = SelectField('科目', choices=[
        ('', '全科'), ('语文', '语文'), ('数学', '数学'), ('英语', '英语')
    ], validators=[Optional()])
    exam_date = DateField('目标考试日期', validators=[DataRequired()])


class MockTestForm(FlaskForm):
    """Mock test form."""
    title = StringField('测试标题', validators=[DataRequired(), Length(max=200)])
    subject = SelectField('科目', choices=[
        ('语文', '语文'), ('数学', '数学'), ('英语', '英语')
    ], validators=[DataRequired()])
    chapter = StringField('章节', validators=[Optional(), Length(max=200)])


class MaterialForm(FlaskForm):
    """Material upload form."""
    auto_analyze = BooleanField('自动AI分析')


class AIConfigForm(FlaskForm):
    """AI configuration form."""
    ai_api_endpoint = StringField('API Endpoint', validators=[Optional()])
    ai_api_key = StringField('API Key', validators=[Optional()])
    ai_model = StringField('默认模型', validators=[Optional()])
    ai_vision_model = StringField('视觉模型', validators=[Optional()])


class SettingsForm(FlaskForm):
    """General settings form."""
    materials_local_dir = StringField('本地资料目录', validators=[Optional()])
