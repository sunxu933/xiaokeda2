# 小课大（xiaokeda）功能设计文档

> 本文档详细描述了"小课大"学习辅导助手应用的完整功能设计，可供开发团队从零重建此系统。

---

## 一、项目概述

### 1.1 产品定位

"小课大"是一款面向中国小学生家长（1-6年级）的 AI 学习辅导 Web 应用。核心目标是帮助家长：

- 管理孩子的作业、试卷等学习资料
- 自动识别和归集错题，建立错题本
- 利用 AI 进行错题讲解、举一反三练习
- 生成个性化复习计划和模拟测试
- 从多份试卷中按题型汇编专项练习 PDF
- 可视化学情报告，发现薄弱环节

### 1.2 目标用户

- **主要用户**：小学生家长（非技术背景）
- **使用场景**：手机端为主、PC 端为辅
- **单用户模式**：无需注册登录，支持多孩子切换

### 1.3 技术栈

| 层面 | 技术选型 | 说明 |
|------|---------|------|
| 后端框架 | Flask 3.x | Python Web 框架 |
| ORM | Flask-SQLAlchemy | 数据库操作 |
| 数据库迁移 | Flask-Migrate | 基于 Alembic |
| 数据库 | SQLite | 单文件数据库，适合单用户 |
| 前端 | Bootstrap 5.3 + Jinja2 | 响应式布局 |
| 图表 | Chart.js | 学情报告可视化 |
| AI 接口 | OpenAI-compatible API | 支持任何 OpenAI 格式的 API（OpenAI、DeepSeek、GLM、MiniMax 等） |
| PDF 生成 | fpdf2 | 中文 PDF 生成 |
| PDF 渲染 | pypdfium2 | PDF 转图片用于 VLM 分析 |
| PDF 文本提取 | pdfplumber / PyPDF2 | PDF 文本提取（双引擎降级） |
| Word 文档 | python-docx | DOCX 文本提取 |
| 图像处理 | Pillow | 图片压缩、格式转换 |

### 1.4 项目目录结构

```
xiaokeda/
├── run.py                          # 启动入口
├── requirements.txt                # Python 依赖
├── .env                            # 环境变量（不提交）
├── .env.example                    # 环境变量模板
├── instance/
│   └── xiaokeda.db                 # SQLite 数据库文件
├── tests/
│   └── test_integration.py         # 集成测试
└── app/
    ├── __init__.py                 # 应用工厂
    ├── config.py                   # 配置类
    ├── extensions.py               # SQLAlchemy / Migrate 实例
    ├── helpers.py                  # 工具函数
    ├── models/                     # 数据模型
    │   ├── student.py              # 学生
    │   ├── homework.py             # 作业
    │   ├── mistake.py              # 错题
    │   ├── material.py             # 学习资料
    │   ├── knowledge.py            # 知识点
    │   ├── review_plan.py          # 复习计划
    │   ├── mock_test.py            # 模拟测试
    │   ├── study_session.py        # 学习记录
    │   ├── ai_log.py               # AI 交互日志
    │   └── settings.py             # 应用设置
    ├── routes/                     # 路由蓝图
    │   ├── main.py                 # 首页/仪表盘
    │   ├── homework.py             # 作业管理
    │   ├── mistakes.py             # 错题本
    │   ├── ai_tutor.py             # AI 辅导
    │   ├── materials.py            # 学习资料
    │   ├── review.py               # 复习/模拟测试
    │   ├── reports.py              # 学情报告
    │   └── settings.py             # 系统设置
    ├── services/                   # 业务逻辑层
    │   ├── ai_service.py           # AI 服务
    │   ├── knowledge_map.py        # 知识点图谱
    │   ├── review_engine.py        # 复习引擎
    │   ├── stats_service.py        # 统计服务
    │   └── pdf_service.py          # PDF 生成服务
    ├── seed_data/
    │   └── knowledge_points.json   # 知识点种子数据
    ├── static/
    │   ├── css/main.css            # 自定义样式
    │   ├── js/app.js               # 客户端脚本
    │   └── uploads/                # 上传文件存储
    │       ├── homework/           # 作业照片
    │       ├── mistakes/           # 错题照片
    │       └── materials/          # 资料文件、渲染页面图片、汇编PDF
    └── templates/                  # Jinja2 模板
        ├── base.html               # 基础布局
        ├── main/                   # 首页模板
        ├── homework/               # 作业模板
        ├── mistakes/               # 错题模板
        ├── ai_tutor/               # AI辅导模板
        ├── materials/              # 资料模板
        ├── review/                 # 复习模板
        ├── reports/                # 报告模板
        └── settings/               # 设置模板
```

---

## 二、系统架构

### 2.1 应用启动流程

1. `run.py` 调用 `create_app()` 创建 Flask 实例
2. `create_app()` 加载配置（从 `.env` 和 `config.py`）
3. 初始化 SQLAlchemy 和 Flask-Migrate
4. 创建上传目录（如不存在）
5. 注册 8 个 Blueprint（各带 URL 前缀）
6. 注册 6 个自定义 Jinja2 模板过滤器
7. 注入全局模板变量（`current_student`、`today`）
8. 注册 404/500 错误处理器
9. `db.create_all()` 创建数据库表
10. `_seed_initial_data()` 初始化默认设置和知识点

### 2.2 Blueprint 注册

| Blueprint | URL 前缀 | 功能 |
|-----------|---------|------|
| main | `/` | 首页仪表盘 |
| homework | `/homework` | 作业管理 |
| mistakes | `/mistakes` | 错题本 |
| ai_tutor | `/ai-tutor` | AI 辅导 |
| materials | `/materials` | 学习资料 |
| review | `/review` | 复习计划 |
| reports | `/reports` | 学情报告 |
| settings | `/settings` | 系统设置 |

### 2.3 自定义模板过滤器

| 过滤器名 | 功能 |
|----------|------|
| `datetimeformat` | 日期时间格式化：`%Y-%m-%d %H:%M` |
| `dateformat` | 日期格式化：`%Y-%m-%d` |
| `subject_color` | 科目→颜色映射（语文=#e74c3c, 数学=#3498db, 英语=#2ecc71） |
| `subject_icon` | 科目→Emoji 图标 |
| `nl2br` | 换行符→`<br>` |
| `from_json` | JSON 字符串解析为 Python 对象 |
| `to_letter` | 整数 0-25 转为字母 A-Z |

### 2.4 全局请求处理

- `@require_student` 装饰器：检查是否有活跃学生配置，无则重定向到设置页
- `inject_globals()`：每个请求自动注入 `g.current_student`
- 无用户认证系统，通过 `AppSetting` 中的 `current_student_id` 切换学生

### 2.5 配置项

| 配置 | 默认值 | 说明 |
|------|--------|------|
| `SECRET_KEY` | 从 .env 读取 | Flask 密钥 |
| `SQLALCHEMY_DATABASE_URI` | `sqlite:///instance/xiaokeda.db` | 数据库路径 |
| `UPLOAD_FOLDER` | `app/static/uploads` | 文件上传根目录 |
| `MAX_CONTENT_LENGTH` | 32MB | 最大上传大小 |
| `ALLOWED_EXTENSIONS` | png/jpg/jpeg/gif/webp/pdf/doc/docx | 允许的文件类型 |

### 2.6 环境变量（.env）

```
FLASK_ENV=development
SECRET_KEY=change-this-to-a-random-string
AI_API_ENDPOINT=https://api.openai.com/v1
AI_API_KEY=
AI_MODEL=gpt-4o
AI_VISION_MODEL=gpt-4o
```

---

## 三、数据库设计

共 11 张表，关系图如下：

```
Student ──1:N── Homework ──1:N── HomeworkItem
   │
   ├──1:N── Mistake
   ├──1:N── StudySession
   ├──1:N── ReviewPlan ──1:N── ReviewTask
   ├──1:N── MockTest ──1:N── MockTestItem
   ├──1:N── AIInteraction
   └──1:N── Material ──1:N── MaterialKnowledge
                       └──1:N── MaterialQuestion

KnowledgePoint ──self_ref── KnowledgePoint
AppSetting (独立)
```

### 3.1 students — 学生表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK, AUTO | 主键 |
| name | String(50) | NOT NULL | 学生姓名 |
| grade | Integer | NOT NULL | 年级（1-6） |
| school | String(100) | | 学校名称 |
| avatar | String(200) | | 头像路径 |
| created_at | DateTime | 默认当前 | 创建时间 |
| updated_at | DateTime | 自动更新 | 更新时间 |

### 3.2 homework — 作业表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK | 主键 |
| student_id | Integer | FK→students | 学生 |
| title | String(200) | NOT NULL | 作业标题 |
| subject | String(20) | NOT NULL | 科目：语文/数学/英语 |
| grade | Integer | | 年级 |
| homework_date | Date | NOT NULL | 作业日期 |
| due_date | Date | | 截止日期 |
| status | String(20) | 默认 pending | pending/in_progress/completed/reviewed |
| total_score | Float | | 实际得分 |
| max_score | Float | | 满分 |
| notes | Text | | 备注 |
| time_spent | Integer | | 用时（分钟） |
| image_path | String(300) | | 上传照片路径 |
| ai_recognition | Text | | AI 识别结果（JSON） |

### 3.3 homework_items — 作业题目表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK | 主键 |
| homework_id | Integer | FK→homework | 所属作业 |
| question_number | Integer | | 题号 |
| content | Text | | 题目内容 |
| is_correct | Boolean | | 是否正确 |
| student_answer | Text | | 学生答案 |
| correct_answer | Text | | 正确答案 |
| mistake_type | String(50) | | 错误类型：calculation/concept/careless/unknown |
| knowledge_point | String(100) | | 关联知识点 |

### 3.4 mistakes — 错题表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK | 主键 |
| student_id | Integer | FK→students | 学生 |
| subject | String(20) | NOT NULL | 科目 |
| grade | Integer | | 年级 |
| topic | String(100) | | 主题（如"两位数乘法"） |
| knowledge_point | String(100) | | 知识点标签 |
| question_text | Text | NOT NULL | 完整题目 |
| student_answer | Text | | 学生错误答案 |
| correct_answer | Text | | 正确答案 |
| explanation | Text | | 解析 |
| source | String(50) | | 来源：manual/homework/mock_test |
| source_id | Integer | | 来源记录ID |
| image_path | String(300) | | 照片路径 |
| ai_analysis | Text | | AI 分析结果（JSON） |
| difficulty | String(20) | | 难度：easy/medium/hard |
| review_count | Integer | 默认 0 | 已复习次数 |
| mastered | Boolean | 默认 False | 是否已掌握 |
| next_review | Date | | 下次复习日期 |

**间隔复习算法**：复习间隔为 [1, 3, 7, 14, 30] 天。完成 5 次复习后自动标记为已掌握。每次 `mark_reviewed()` 调用递增 `review_count` 并计算 `next_review = today + intervals[min(count, len(intervals)-1)]`。

### 3.5 materials — 学习资料表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK | 主键 |
| student_id | Integer | FK→students | 学生 |
| title | String(200) | NOT NULL | 资料标题 |
| subject | String(20) | | 科目 |
| material_type | String(30) | | 类型：试卷/练习册/讲义/课本/笔记/其他 |
| file_path | String(300) | | 文件存储路径 |
| file_type | String(20) | | 文件格式：image/pdf/docx |
| description | Text | | 描述 |
| source_grade | Integer | | 适用年级 |
| source_semester | String(10) | | 学期：上册/下册 |
| source_chapter | String(200) | | 章节 |
| ai_analysis | Text | | AI 分析结果（JSON） |
| page_images | Text | | 页面图片路径（JSON 数组） |
| status | String(20) | 默认 pending | pending/analyzing/analyzed/failed/archived |
| tags | String(200) | | 标签（逗号分隔） |

### 3.6 material_knowledge — 资料知识点表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK | 主键 |
| material_id | Integer | FK→materials | 所属资料 |
| subject | String(20) | | 科目 |
| chapter | String(200) | | 章节 |
| topic | String(200) | | 知识点主题 |
| content | Text | | 详细内容 |
| key_formulas | Text | | 关键公式（JSON 数组） |
| key_points | Text | | 要点（JSON 数组） |
| difficulty | String(20) | | 难度 |
| importance | String(20) | | 重要性：core/important/supplementary |

### 3.7 material_questions — 资料题目表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK | 主键 |
| material_id | Integer | FK→materials | 所属资料 |
| question_text | Text | | 题目内容 |
| answer | Text | | 正确答案 |
| explanation | Text | | 解析 |
| question_type | String(30) | | 题型：choice/fill_blank/calculation/essay |
| knowledge_point | String(200) | | 知识点 |
| difficulty | String(20) | | 难度 |
| options | Text | | 选择题选项（JSON 数组） |
| page_number | Integer | | 所在页码 |
| score | Float | | 分值 |
| ai_generated | Boolean | | AI 提取 |

### 3.8 knowledge_points — 知识点表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK | 主键 |
| subject | String(20) | NOT NULL | 科目 |
| grade | Integer | NOT NULL | 年级（1-6） |
| semester | String(10) | | 学期：上册/下册 |
| chapter | String(100) | | 章节名 |
| topic | String(100) | | 具体知识点 |
| description | Text | | 描述 |
| parent_id | Integer | FK→knowledge_points | 父级知识点（自引用） |
| sort_order | Integer | | 排序序号 |

### 3.9 review_plans + review_tasks — 复习计划表

**review_plans：**

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK | 主键 |
| student_id | Integer | FK→students | 学生 |
| title | String(200) | NOT NULL | 计划标题 |
| subject | String(20) | | 科目（空=全科） |
| exam_date | Date | | 目标考试日期 |
| start_date | Date | | 开始日期 |
| end_date | Date | | 结束日期 |
| status | String(20) | 默认 draft | draft/active/completed |
| total_tasks | Integer | | 总任务数 |
| completed_tasks | Integer | 默认 0 | 已完成任务数 |
| ai_generated | Boolean | | 是否 AI 生成 |

**review_tasks：**

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK | 主键 |
| plan_id | Integer | FK→review_plans | 所属计划 |
| day_number | Integer | | 天数序号 |
| scheduled_date | Date | | 计划日期 |
| subject | String(20) | | 科目 |
| topic | String(100) | | 复习主题 |
| task_type | String(30) | | review_mistakes/practice/mock_test/knowledge_review |
| description | Text | | 任务描述 |
| knowledge_point | String(100) | | 知识点 |
| status | String(20) | 默认 pending | pending/completed/skipped |
| time_spent | Integer | | 用时（分钟） |
| mistake_ids | Text | | 关联错题ID（JSON 数组） |
| completed_at | DateTime | | 完成时间 |

### 3.10 mock_tests + mock_test_items — 模拟测试表

**mock_tests：**

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK | 主键 |
| student_id | Integer | FK→students | 学生 |
| plan_id | Integer | FK→review_plans | 关联复习计划（可选） |
| subject | String(20) | | 科目 |
| grade | Integer | | 年级 |
| title | String(200) | | 测试标题 |
| total_questions | Integer | | 总题数 |
| score | Float | | 得分 |
| max_score | Float | 默认 100 | 满分 |
| time_limit | Integer | | 时间限制（分钟） |
| time_spent | Integer | | 实际用时 |
| status | String(20) | | draft/in_progress/completed |
| chapter | String(200) | | 章节 |
| ai_prompt_used | Text | | 使用的 AI 提示词 |

**mock_test_items：**

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK | 主键 |
| mock_test_id | Integer | FK→mock_tests | 所属测试 |
| question_number | Integer | | 题号 |
| question_text | Text | | 题目内容 |
| answer | Text | | 正确答案 |
| options | Text | | 选项（JSON） |
| question_type | String(30) | | 题型 |
| student_answer | Text | | 学生答案 |
| is_correct | Boolean | | 是否正确 |
| knowledge_point | String(100) | | 知识点 |
| difficulty | String(20) | | 难度 |
| explanation | Text | | 解析 |
| score | Float | | 得分 |
| max_score | Float | | 分值 |
| ai_generated | Boolean | | AI 生成 |

### 3.11 study_sessions + ai_interactions + app_settings

**study_sessions — 学习记录表：**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer PK | 主键 |
| student_id | Integer FK | 学生 |
| subject | String(20) | 科目 |
| session_type | String(30) | homework/review/practice/mock_test |
| start_time | DateTime | 开始时间 |
| end_time | DateTime | 结束时间 |
| duration | Integer | 时长（分钟） |
| notes | Text | 备注 |
| related_id | Integer | 关联实体ID |

**ai_interactions — AI 交互日志表：**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer PK | 主键 |
| student_id | Integer FK | 学生（可选） |
| interaction_type | String(30) | 交互类型 |
| subject | String(20) | 科目 |
| prompt_text | Text | 输入提示 |
| response_text | Text | AI 响应 |
| image_path | String(300) | 图片路径 |
| model_used | String(50) | 模型标识 |
| tokens_used | Integer | Token 消耗 |
| duration_ms | Integer | 响应耗时（毫秒） |
| related_id | Integer | 关联实体ID |
| created_at | DateTime | 创建时间 |

**app_settings — 应用设置表：**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer PK | 主键 |
| key | String(100) UNIQUE | 设置键 |
| value | Text | 设置值 |
| description | String(200) | 说明 |
| updated_at | DateTime | 更新时间 |

预置设置项：`ai_api_endpoint`、`ai_api_key`、`ai_model`、`ai_vision_model`、`daily_study_goal_minutes`（默认60）、`current_student_id`、`materials_local_dir`。

---

## 四、功能模块详细设计

### 4.1 首页仪表盘（main）

**路由：** `GET /`

**功能：** 展示今日概览信息

**数据加载：**
- 今日作业列表（`Homework` where homework_date = today）
- 今日学习时长（`StudySession` 聚合）
- 待处理任务数量
- 今日到期需复习的错题（`Mistake.get_due_for_review()`）
- 进行中的复习计划

**模板：** `main/index.html`

### 4.2 作业管理（homework）

#### 路由清单

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | `/homework/` | 作业列表（支持科目/状态/日期筛选） |
| GET/POST | `/homework/add` | 新建作业 |
| GET | `/homework/<id>` | 作业详情（含题目列表） |
| GET/POST | `/homework/<id>/edit` | 编辑作业 |
| POST | `/homework/<id>/delete` | 删除作业 |
| POST | `/homework/<id>/status` | 更新状态（完成时自动记录学习时长） |
| POST | `/homework/<id>/items` | 添加题目项（AJAX） |
| PUT | `/homework/<id>/items/<item_id>` | 更新题目项（AJAX） |
| POST | `/homework/<id>/extract-mistakes` | 提取错题到错题本 |
| POST | `/homework/recognize-photo` | 拍照 AI 识别（返回JSON） |

#### 拍照识别流程

1. 前端上传图片到 `POST /homework/recognize-photo`
2. 后端调用 `ai_service.recognize_homework(图片路径, 年级)`
3. AI 返回科目和题目列表（JSON）
4. 前端展示识别结果供确认
5. 用户确认后提交，创建 Homework + HomeworkItem

#### 错题提取逻辑

1. 遍历 Homework 中 `is_correct = False` 的 HomeworkItem
2. 为每个错误项创建 `Mistake` 记录，设置 `source='homework'`
3. 错题的 `topic`、`knowledge_point` 从 HomeworkItem 继承
4. 一次性批量创建，页面重定向到错题列表

### 4.3 错题本（mistakes）

#### 路由清单

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | `/mistakes/` | 错题列表（筛选：科目/主题/掌握状态） |
| GET/POST | `/mistakes/add` | 手动添加错题 |
| GET | `/mistakes/<id>` | 错题详情 |
| GET/POST | `/mistakes/<id>/edit` | 编辑错题 |
| POST | `/mistakes/<id>/delete` | 删除错题 |
| POST | `/mistakes/<id>/mark-mastered` | 标记已掌握 |
| POST | `/mistakes/<id>/mark-reviewed` | 标记已复习（触发间隔复习算法） |
| GET | `/mistakes/by-topic` | 按科目和主题分组浏览 |
| GET | `/mistakes/review-due` | 今日到期需复习的错题 |

#### 间隔复习算法

```python
INTERVALS = [1, 3, 7, 14, 30]  # 天

def mark_reviewed(self):
    self.review_count += 1
    if self.review_count >= 5:
        self.mastered = True
    idx = min(self.review_count - 1, len(INTERVALS) - 1)
    self.next_review = date.today() + timedelta(days=INTERVALS[idx])
```

- 第 1 次复习 → 1 天后再复习
- 第 2 次 → 3 天后
- 第 3 次 → 7 天后
- 第 4 次 → 14 天后
- 第 5 次 → 30 天后，同时标记为已掌握

### 4.4 AI 辅导（ai_tutor）

#### 路由清单

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | `/ai-tutor/` | AI 聊天界面 |
| GET | `/ai-tutor/explain/<mistake_id>` | 错题讲解页面 |
| GET | `/ai-tutor/practice/<mistake_id>` | 举一反三练习页面 |
| POST | `/ai-tutor/chat` | AI 聊天（JSON API） |
| POST | `/ai-tutor/analyze-photo` | 拍照分析（JSON API） |
| POST | `/ai-tutor/explain/<id>/generate` | 生成讲解（JSON API） |
| POST | `/ai-tutor/practice/<id>/generate` | 生成类似题（JSON API） |
| POST | `/ai-tutor/generate-practice` | 按主题生成练习（JSON API） |
| GET | `/ai-tutor/history` | AI 交互历史 |

#### 交互流程

**错题讲解**：用户点击错题详情中的"AI 讲解"按钮 → 前端请求 `explain/<id>/generate` → 后端调用 `ai_service.explain_problem()` → 返回分步讲解文本

**举一反三**：用户点击"举一反三"按钮 → 前端请求 `practice/<id>/generate` → 后端调用 `ai_service.generate_similar_problems()` → 返回 JSON 格式的类似题目（默认 3 道）

**拍照分析**：上传图片 → `ai_service.analyze_photo()` → 识别题目内容并返回

### 4.5 学习资料（materials）

#### 路由清单

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | `/materials/` | 资料列表（筛选：科目/类型/状态） |
| GET/POST | `/materials/upload` | 上传资料（支持多文件+自动分析） |
| GET | `/materials/<id>` | 资料详情 |
| GET | `/materials/<id>/preview` | 在线预览文件 |
| POST | `/materials/<id>/analyze` | 触发 AI 分析 |
| POST | `/materials/<id>/delete` | 删除资料 |
| GET | `/materials/knowledge-base` | 知识库树形浏览 |
| GET | `/materials/knowledge-base/search` | 搜索知识库（JSON） |
| POST | `/materials/generate-questions` | 从知识库生成练习（JSON） |
| GET | `/materials/browse` | 本地目录浏览 |
| GET | `/materials/browse/api/list` | 目录列表（JSON） |
| POST | `/materials/browse/api/import` | 从本地导入文件（JSON） |
| POST | `/materials/browse/api/set-base-dir` | 设置浏览根目录（JSON） |
| GET | `/materials/compile` | 题型汇编页面 |
| POST | `/materials/compile/api/types` | 题型汇总（JSON） |
| POST | `/materials/compile/api/generate` | 生成汇编 PDF（JSON） |
| GET | `/materials/compile/preview/<uuid>` | PDF 预览 |

#### AI 分析流程（核心，约 300 行代码）

这是系统最复杂的流程。函数 `_analyze_material(material, student)`：

**Step 1 — 分发处理（按文件类型）：**

- **图片类型（image）**：直接调用 `ai_service.analyze_material_image()`，一次 VLM 调用完成全部提取
- **PDF 类型**：
  1. 使用 `pypdfium2` 将 PDF 每页渲染为 JPEG 图片（最多 10 页）
  2. 第 1 页：调用 `analyze_material_image()`（提取完整元数据 + 知识点 + 题目）
  3. 第 2+ 页：调用 `analyze_pdf_page()`（仅提取题目和知识点）
  4. 使用 `_merge_page_results()` 合并结果，按 topic 去重知识点
  5. 页面图片路径存储到 `material.page_images`（JSON 数组）
- **DOCX 类型**：使用 `python-docx` 提取文本（最多 10000 字符），调用 `analyze_text_content()`
- **PDF 文本降级**：如 pypdfium2 不可用，用 `pdfplumber`（主）/ `PyPDF2`（备）提取文本

**Step 2 — 二次题目提取：**

若第一遍未提取到题目（PDF/DOCX），调用 `extract_questions_from_text()` 专门提取题目。对图片类型则用 VLM 做直接题目提取。

**Step 3 — 元数据推断：**

`_infer_metadata_from_title()` 用正则从文件名推断：
- 科目（数学/语文/英语）
- 年级（支持 "3年级" 和 "三年级" 两种写法）
- 学期（上册/下册）
- 资料类型（试卷/练习册/讲义等）

**Step 4 — 存储结果：**

创建 `MaterialKnowledge` 和 `MaterialQuestion` 记录，更新 Material 的元数据和状态。

#### 题型汇编 PDF 生成流程

1. 用户选择多份已分析资料 + 题型
2. 系统查询 `MaterialQuestion`（按 material_id + question_type 筛选）
3. 按来源资料分组为 sections
4. 调用 `CompilationPDF.build()` 生成 PDF
5. PDF 保存为 `compiled_{uuid}.pdf`
6. 自动清理超过 1 小时的旧汇编 PDF

#### 本地目录浏览

- 安全措施：`os.path.realpath()` 防止路径遍历
- 浏览根目录通过 `AppSetting` 的 `materials_local_dir` 配置
- 导入时将文件复制到 uploads 目录并创建 Material 记录

### 4.6 复习与模拟测试（review）

#### 路由清单

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | `/review/` | 复习计划列表 |
| GET/POST | `/review/create` | 创建复习计划 |
| GET | `/review/plan/<id>` | 计划详情（按日分组） |
| POST | `/review/plan/<id>/task/<tid>/complete` | 完成任务 |
| POST | `/review/plan/<id>/task/<tid>/skip` | 跳过任务 |
| POST | `/review/plan/<id>/delete` | 删除计划 |
| GET | `/review/knowledge-summary` | 知识点汇总 |
| POST | `/review/knowledge-summary/generate` | AI 生成知识汇总（JSON） |
| GET | `/review/practice` | 章节练习 |
| POST | `/review/practice/generate` | 生成练习题（JSON） |
| GET/POST | `/review/mock-test/create` | 创建模拟测试 |
| GET | `/review/mock-test/<id>` | 参加测试 |
| POST | `/review/mock-test/<id>/submit` | 提交答案 |
| GET | `/review/mock-test/<id>/result` | 查看结果 |
| GET | `/review/mock-tests` | 测试列表 |

#### 复习计划生成算法

`auto_generate_plan(student_id, title, exam_date, subject)`:

1. **校验**：考试日期距今至少 3 天，预留最后 2 天做模拟测试
2. **数据收集**：查询所有未掌握的 Mistake
3. **主题优先级排序**：按 `subject|topic` 分组，`priority = count × 3`
4. **任务分配**：
   - 前半天数每天安排 1-2 个主题（高优先级优先）
   - 每天的任务类型：`review_mistakes`（复习错题）+ `practice`（练习）
   - 后半天数安排剩余主题或"综合复习"
5. **模拟测试日**：最后 2 天设为 `mock_test` 任务

无错题时降级为 `_generate_knowledge_review_plan()`：按知识点均匀分配。

#### 模拟测试流程

**创建**：
1. 收集主题（从表单或知识点库）
2. 调用 `generate_mock_test_from_plan()` → AI 生成题目
3. 创建 `MockTest` + `MockTestItem` 记录

**答题**：前端渲染题目和输入框

**提交和评分**：
1. **评分方式**：精确字符串匹配（`answer.strip() == correct_answer.strip()`）
2. **计分**：正确得满分，错误得 0 分
3. **错题入库**：每道错题自动创建 `Mistake` 记录，来源标记为 `mock_test`

### 4.7 学情报告（reports）

#### 路由清单

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | `/reports/` | 报告仪表盘（含图表） |
| GET | `/reports/weak-areas` | 薄弱环节详情 |
| GET | `/reports/api/study-time` | 学习时长数据（JSON） |
| GET | `/reports/api/mistake-distribution` | 错题分布（JSON） |
| GET | `/reports/api/subject-comparison` | 学科对比（JSON） |
| GET | `/reports/api/weekly-summary` | 周报数据（JSON） |

#### 统计计算逻辑

**学习时长** `get_study_time_summary(student_id, start, end)`：
- 按日期和科目聚合 `StudySession.duration`
- 返回 30 天内每日各科目学习分钟数

**错题分布** `get_mistake_distribution(student_id, start, end)`：
- 按科目、难度、主题分组统计
- 计算掌握率：`mastered / total × 100`

**薄弱环节** `get_weak_areas(student_id, top_n=10)`：
- SQL GROUP BY `(subject, topic)` 聚合
- 优先级公式：`unmastered_count × 3 + total_count × 1`
- 返回前 N 个最薄弱主题

**学科对比** `get_subject_comparison(student_id)`：
- 各科五维指标：错题数、掌握率、作业数、作业完成率、近30天学习时长
- 用于雷达图展示

**周报** `get_weekly_summary(student_id, weeks=4)`：
- 最近 N 周（周一到周日）的错题数、学习时长、作业数

### 4.8 系统设置（settings）

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | `/settings/` | 设置概览 |
| GET/POST | `/settings/student` | 学生档案管理（增删改+切换） |
| POST | `/settings/student/<id>/select` | 切换活跃学生 |
| POST | `/settings/student/<id>/delete` | 删除学生 |
| GET/POST | `/settings/ai-config` | AI API 配置 |
| POST | `/settings/ai-test` | 测试 AI 连接（JSON） |
| GET | `/settings/export` | 数据导出页 |
| POST | `/settings/export/db` | 下载数据库备份文件 |

---

## 五、AI 服务层设计

### 5.1 架构

`AIService` 类，全局单例 `ai_service`。

- **兼容性**：支持任何 OpenAI 格式的 API（OpenAI、DeepSeek、GLM、Ollama、MiniMax）
- **MiniMax VLM 特殊处理**：当 API 端点包含 `minimaxi.com` 或 `minimax.io` 时，使用专用 VLM 端点 `/v1/coding_plan/vlm`
- **图片压缩**：发送前自动压缩图片（最大 1568px，JPEG quality=85）
- **日志记录**：所有 AI 调用记录到 `ai_interactions` 表

### 5.2 API 调用方式

| 方法 | 调用方式 | 温度 | 用途 |
|------|---------|------|------|
| `_call_text()` | 文本 ChatCompletion | 0.7 | 解释、聊天、文本分析 |
| `_call_vision()` | 多模态 ChatCompletion | 0.3 | 图片识别、VLM 分析 |
| `_call_vlm()` | MiniMax 专用 VLM 端点 | 0.3 | MiniMax 图片分析 |

### 5.3 AI 方法清单与 Prompt 设计要点

| 方法 | Prompt 要点 | 输出格式 |
|------|-------------|----------|
| `analyze_photo(图片, 年级)` | 按年级分析题目，逐题给出答案 | JSON: `{questions: [{content, answer, ...}]}` |
| `recognize_homework(图片, 年级)` | 先判科目再提取题目 | JSON: `{subject, questions: [...]}` |
| `explain_problem(题目, 答案, 年级)` | 友好教师语气，分步讲解 | 纯文本 |
| `analyze_mistake(题目, 错答, 正答)` | 诊断错误类型和根因 | JSON: `{error_type, root_cause, weak_point, suggestion}` |
| `generate_similar_problems(题目, 数量)` | 考官角色，生成变体题 | JSON: `{problems: [{question, answer, ...}]}` |
| `generate_practice_by_topic(主题, 科目, 年级)` | 混合题型生成 | JSON: `{problems: [{type, question, options, answer, ...}]}` |
| `generate_mock_test(主题列表, 科目, 年级)` | 难度分布 30%易/50%中/20%难，满分100 | JSON: `{title, questions: [{type, question, options, answer, score, ...}]}` |
| `generate_knowledge_summary(章节, 科目)` | 教学专家，含记忆技巧 | 纯文本 |
| `analyze_material_image(图片, 年级)` | 结构化提取元数据+知识点+题目 | JSON: `{material_type, subject, knowledge_points, questions}` |
| `analyze_pdf_page(图片, 页码)` | 第2+页分析，检测答案页并跳过 | JSON: `{questions, knowledge_points}` |
| `analyze_text_content(文本, 年级)` | 与图片分析同结构 | JSON（同上） |
| `extract_questions_from_text(文本)` | 专注题目提取 | JSON 数组 |
| `generate_questions_from_knowledge(知识点列表)` | 基于知识生成题目 | JSON: `{questions: [...]}` |
| `chat(消息列表, 年级, 科目)` | 辅导教师角色 | 纯文本 |

### 5.4 JSON 提取容错

`_extract_json(text)` 按优先级尝试 4 种策略：
1. 直接 `json.loads()`
2. Markdown 代码块提取（` ```json ... ``` `）
3. 括号匹配扫描（`{...}` / `[...]`）
4. 返回 `None`

---

## 六、PDF 编译服务设计

### 6.1 CompilationPDF 类

使用 `fpdf2` 库 + Windows 系统字体（微软雅黑 `msyh.ttc` 或黑体 `simhei.ttf`）。

### 6.2 核心处理流程

```python
def build(title, sections, include_answers=True) -> bytes
```

**输入：**
- `title`: 标题（如"计算题专项练习"）
- `sections`: `[{"material_title": str, "material": Material, "questions": [MaterialQuestion]}]`

**处理步骤：**

1. **答案区过滤**：
   - `_find_answer_section_start()`: 在 Material 的全部题目中找到第一个答案区题目所在页码
   - `_filter_answer_pages()`: 移除该页码及之后的所有题目
   - `_is_likely_answer_section()`: 内容级检测（关键词匹配 + 解释性文本模式识别）

2. **去重**：
   - 移除包含 3+ 子题标记的聚合题
   - 前缀重叠去重：如果两题文本的前缀互相包含，保留较短的

3. **题目文本清洗** `_clean_question_text()`：
   - 移除分数标记（"(5分)"）
   - LaTeX 转换（`$\square$` → `□`）
   - 移除章节标题（"四、解决问题"）
   - 移除章节引用（"（一、选择题 第1题）"）
   - 移除题号前缀

4. **子题上下文合并** `_extract_shared_context()`：
   - 检测共享前缀（长度 >15 字符且在子题标记之前）
   - 后续子题只显示差异部分，避免重复背景

5. **图片嵌入**：
   - 检测题目文本中的图片引用（"如图"、"图示"、"方格"等）
   - 通过 `material.page_images` 获取题目所在页的图片路径
   - 嵌入图片：宽度 = 页面可用宽度的 55%，最大高度 90pt

6. **PDF 结构**：
   - 封面页：标题、总题数、来源试卷数
   - 题目页：顺序编号，解答题独占一页，其他题型紧凑排列
   - 参考答案页：答案 + 解析（灰色小字）

---

## 七、前端页面清单

共 35 个模板文件，基于 `base.html`（Bootstrap 5.3 导航栏 + 侧边栏）。

### 7.1 通用模板

| 模板 | 说明 |
|------|------|
| `base.html` | 基础布局：顶部导航栏（7个入口）、Bootstrap 5.3 CDN、移动端响应式 |
| `404.html` | 404 错误页 |
| `500.html` | 500 错误页 |

### 7.2 功能页面（按模块）

| 模板路径 | 功能 | 关键交互 |
|----------|------|----------|
| `main/index.html` | 仪表盘 | 今日统计卡片、待办事项列表 |
| `main/no_student.html` | 无学生提示 | 引导创建学生 |
| `homework/list.html` | 作业列表 | 科目/状态/日期筛选 |
| `homework/add.html` | 新建作业 | 图片上传+AI识别、手动填写 |
| `homework/detail.html` | 作业详情 | 题目列表、逐题评分、提取错题 |
| `homework/edit.html` | 编辑作业 | 表单 |
| `mistakes/list.html` | 错题列表 | 科目/主题/掌握状态筛选 |
| `mistakes/add.html` | 添加错题 | 图片上传、知识点自动补全 |
| `mistakes/detail.html` | 错题详情 | AI讲解/举一反三按钮、关联错题 |
| `mistakes/edit.html` | 编辑错题 | 表单 |
| `mistakes/by_topic.html` | 按主题分组 | 树形展示 |
| `mistakes/review_due.html` | 到期复习 | 复习操作按钮 |
| `ai_tutor/chat.html` | AI 聊天 | 对话式交互、支持拍照上传 |
| `ai_tutor/explain.html` | AI 讲解 | 展示分步讲解内容 |
| `ai_tutor/practice.html` | 举一反三 | 展示生成的类似题目 |
| `ai_tutor/history.html` | 交互历史 | 时间线展示 |
| `materials/list.html` | 资料列表 | 状态/类型/科目筛选、统计卡片 |
| `materials/upload.html` | 上传资料 | 多文件上传、自动分析开关 |
| `materials/detail.html` | 资料详情 | 预览、知识点列表、题目表格、AI分析 |
| `materials/browse.html` | 本地浏览 | 面包屑导航、文件勾选、批量导入 |
| `materials/compile.html` | 题型汇编 | 三步向导：选试卷→选题型→生成预览 |
| `materials/knowledge_base.html` | 知识库 | 树形结构浏览 |
| `materials/practice.html` | 知识库练习 | 选择章节→AI生成练习 |
| `review/plans.html` | 复习计划列表 | 进度条、状态筛选 |
| `review/create_plan.html` | 创建计划 | 科目+考试日期选择 |
| `review/plan_detail.html` | 计划详情 | 按日分组、任务完成/跳过 |
| `review/knowledge_summary.html` | 知识汇总 | 按章节展示+AI生成 |
| `review/practice.html` | 章节练习 | 选择主题→生成练习 |
| `review/create_mock_test.html` | 创建测试 | 配置科目/年级/章节 |
| `review/mock_test.html` | 参加测试 | 逐题作答界面 |
| `review/mock_test_result.html` | 测试结果 | 得分、逐题结果 |
| `review/mock_test_list.html` | 测试历史 | 历次测试列表 |
| `reports/dashboard.html` | 报告仪表盘 | Chart.js 图表 |
| `reports/weak_areas.html` | 薄弱环节 | 优先级排序的薄弱点列表 |
| `settings/index.html` | 设置概览 | 导航卡片 |
| `settings/student_profile.html` | 学生档案 | 增删改+切换 |
| `settings/ai_config.html` | AI 配置 | 端点/密钥/模型设置+连接测试 |
| `settings/export.html` | 数据导出 | 数据库备份下载 |

---

## 八、种子数据

### 8.1 知识点种子数据

文件：`app/seed_data/knowledge_points.json`

包含小学 1-6 年级三科的完整课程知识点，结构为：

```json
{
  "数学": {
    "1": {
      "上册": [{"chapter": "准备课", "topics": ["数一数", "比多少"]}],
      "下册": [...]
    },
    "2": {...},
    ...
  },
  "语文": {...},
  "英语": {...}
}
```

首次启动时由 `_seed_initial_data()` 导入到 `knowledge_points` 表（仅在表为空时导入）。

### 8.2 应用设置种子数据

首次启动时创建 7 个默认设置项：

| Key | 默认值 |
|-----|--------|
| `ai_api_endpoint` | `https://api.openai.com/v1` |
| `ai_api_key` | 空 |
| `ai_model` | `gpt-4o` |
| `ai_vision_model` | `gpt-4o` |
| `daily_study_goal_minutes` | `60` |
| `current_student_id` | 空 |
| `materials_local_dir` | 空 |

---

## 九、部署与运行

### 9.1 环境要求

- Python 3.11+
- Windows Server / Windows（字体依赖：`msyh.ttc` 微软雅黑）
- 至少 500MB 磁盘空间（用于上传文件和渲染图片）

### 9.2 安装步骤

```bash
# 1. 克隆代码
git clone <repo>
cd xiaokeda

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env 填入 AI API 密钥

# 5. 初始化数据库（自动完成，无需手动）
# 首次启动时 create_app() 会自动创建表和种子数据

# 6. 启动
python run.py
# 访问 http://localhost:5000
```

### 9.3 依赖清单

```
Flask>=3.0.0
Flask-SQLAlchemy>=3.0.0
Flask-Migrate>=4.0.0
openai>=1.0.0
Pillow>=10.0.0
python-dotenv>=1.0.0
PyPDF2>=3.0.0
pdfplumber>=0.10.0
python-docx>=1.0.0
fpdf2>=2.8.0
```

另需手动安装（requirements.txt 中未列出但代码引用）：`pypdfium2`、`requests`

### 9.4 数据库迁移

```bash
flask db init        # 初始化迁移目录（仅首次）
flask db migrate     # 生成迁移脚本
flask db upgrade     # 执行迁移
```

### 9.5 测试

```bash
python -m pytest tests/test_integration.py -v
```

集成测试覆盖 12 个测试类、100+ 测试用例，涵盖全部模块的 CRUD、业务逻辑和边界场景。
