# 小课大（xiaokeda2）

> 面向中国小学生家长（1-6年级）的 AI 学习辅导 Web 应用

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0+-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 功能特性

### 核心功能

| 功能 | 说明 |
|------|------|
| **作业管理** | 拍照上传、AI 自动识别题目内容，支持按科目/日期/状态筛选 |
| **错题本** | 自动归集作业和测试中的错题，支持间隔复习算法（艾宾浩斯遗忘曲线） |
| **AI 辅导** | AI 详细讲解错题、智能举一反三生成类似练习题 |
| **学习资料** | 上传 PDF/Word/图片，AI 自动分析提取知识点和题目 |
| **复习计划** | AI 根据错题分布自动生成个性化复习计划 |
| **模拟测试** | AI 生成模拟试卷，支持在线答题和自动评分 |
| **学情报告** | 可视化展示学习时长、错题分布、薄弱环节 |
| **题型汇编** | 按题型（计算/选择/填空等）从多份试卷汇编专项练习 PDF |

### 技术亮点

- **AI 兼容性**：支持任意 OpenAI 格式的 API（OpenAI、DeepSeek、GLM、MiniMax、Ollama 等）
- **PDF 智能处理**：pypdfium2 渲染 + VLM 多模态分析，支持答案页自动检测跳过
- **间隔复习算法**：错题按 [1, 3, 7, 14, 30] 天间隔提醒，5 次掌握后自动标记
- **中文 PDF 生成**：基于 fpdf2 + 微软雅黑字体，生成标准中文试卷

---

## 技术栈

| 层面 | 技术选型 |
|------|---------|
| 后端框架 | Flask 3.x (Python) |
| ORM | Flask-SQLAlchemy |
| 数据库 | SQLite（单文件，适合单用户） |
| 前端 | Bootstrap 5.3 + Jinja2 模板 |
| 图表 | Chart.js |
| AI 接口 | OpenAI-compatible API（支持多模型） |
| PDF 生成 | fpdf2 |
| PDF 渲染 | pypdfium2 |
| PDF 文本提取 | pdfplumber / PyPDF2 |
| Word 文档 | python-docx |
| 图片处理 | Pillow |

---

## 目录结构

```
xiaokeda2/
├── run.py                      # 应用入口
├── requirements.txt            # Python 依赖
├── .env.example                # 环境变量模板
├── .gitignore                  # Git 忽略文件
├── instance/                   # 数据库文件目录
│   └── xiaokeda.db
├── app/
│   ├── __init__.py             # 应用工厂
│   ├── config.py               # 配置类
│   ├── extensions.py           # SQLAlchemy / Migrate 实例
│   ├── helpers.py              # 工具函数
│   ├── forms.py                # WTForms 表单
│   ├── models/                 # 数据模型
│   │   ├── student.py          # 学生
│   │   ├── homework.py         # 作业
│   │   ├── mistake.py          # 错题
│   │   ├── material.py         # 学习资料
│   │   ├── knowledge.py        # 知识点
│   │   ├── review_plan.py      # 复习计划
│   │   ├── mock_test.py        # 模拟测试
│   │   ├── study_session.py    # 学习记录
│   │   ├── ai_log.py           # AI 交互日志
│   │   └── settings.py         # 应用设置
│   ├── routes/                 # 路由蓝图
│   │   ├── main.py             # 首页/仪表盘
│   │   ├── homework.py         # 作业管理
│   │   ├── mistakes.py         # 错题本
│   │   ├── ai_tutor.py         # AI 辅导
│   │   ├── materials.py        # 学习资料
│   │   ├── review.py           # 复习/模拟测试
│   │   ├── reports.py          # 学情报告
│   │   └── settings.py         # 系统设置
│   ├── services/               # 业务逻辑层
│   │   ├── ai_service.py       # AI 服务
│   │   ├── knowledge_map.py    # 知识点图谱
│   │   ├── review_engine.py    # 复习引擎
│   │   ├── stats_service.py    # 统计服务
│   │   └── pdf_service.py      # PDF 生成服务
│   ├── seed_data/
│   │   └── knowledge_points.json  # 知识点种子数据
│   ├── static/
│   │   ├── css/main.css
│   │   ├── js/app.js
│   │   └── uploads/            # 上传文件存储
│   └── templates/              # Jinja2 模板（共 35 个）
└── tests/                      # 测试文件
```

---

## 快速开始

### 环境要求

- Python 3.11+
- Windows / Linux / macOS

### 安装步骤

```bash
# 1. 克隆项目
git clone https://github.com/sunxu933/xiaokeda2.git
cd xiaokeda2

# 2. 创建虚拟环境
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env，填入你的 AI API Key：
# AI_API_KEY=sk-xxxxxxxxxxxx

# 5. 启动应用
python run.py

# 6. 打开浏览器访问
# http://localhost:5000
```

### 首次使用

1. 首次启动后会自动创建 SQLite 数据库
2. 访问 http://localhost:5000 会跳转到学生设置页面
3. 添加一个学生（姓名、年级）
4. 配置 AI API（设置 → AI 配置，填入 API Key 和端点）
5. 开始使用！

---

## 配置说明

### 环境变量（.env）

```env
FLASK_ENV=development          # 开发/生产环境
SECRET_KEY=change-this         # Flask 密钥，请修改为随机字符串
AI_API_ENDPOINT=https://api.openai.com/v1   # AI API 端点
AI_API_KEY=                    # 你的 API Key（必填）
AI_MODEL=gpt-4o                # 文本模型
AI_VISION_MODEL=gpt-4o         # 视觉模型
```

### AI API 配置

系统支持任何 OpenAI 兼容 API，以下是常用配置示例：

| 服务商 | Endpoint |
|--------|----------|
| OpenAI | `https://api.openai.com/v1` |
| DeepSeek | `https://api.deepseek.com/v1` |
| 硅基流动 | `https://api.siliconflow.cn/v1` |
| MiniMax | `https://api.minimaxi.com/v1` |
| Ollama (本地) | `http://localhost:11434/v1` |

---

## 主要功能说明

### 作业管理

1. **拍照上传**：拍摄作业照片，AI 自动识别科目和题目
2. **手动录入**：直接填写作业信息
3. **错题提取**：完成作业后一键将错题归集到错题本

### 错题本

- **间隔复习**：遵循遗忘曲线规律，系统会在 [1, 3, 7, 14, 30] 天后提醒复习
- **AI 讲解**：点击任意错题获取详细的分步讲解
- **举一反三**：AI 生成同类型变式练习题
- **按主题整理**：错题按科目+知识点分组，便于专项突破

### 学习资料

支持的格式：
- **图片**：JPG、PNG、JPEG、GIF、WebP
- **PDF**：自动逐页渲染分析
- **Word**：DOCX 文档

上传后 AI 自动：
- 识别资料类型（试卷/练习册/讲义等）
- 提取知识点
- 提取全部题目
- 检测答案页并自动跳过

### 题型汇编

从多份已分析的试卷中，按题型选择题目，生成专项练习 PDF：

1. 选择多份资料
2. 选择题型（计算题/选择题/填空题/解答题）
3. 生成预览 → 下载 PDF

### 复习计划

1. 设置目标考试日期
2. AI 分析历史错题分布
3. 自动生成每日复习任务
4. 支持：错题复习、章节练习、模拟测试

---

## 数据导出

定期备份数据库：
- 设置 → 数据导出 → 下载数据库备份

---

## 开发

### 运行测试

```bash
python -m pytest tests/ -v
```

### 数据库迁移

```bash
# 初始化（仅首次）
flask db init

# 生成迁移脚本
flask db migrate -m "描述"

# 执行迁移
flask db upgrade
```

### 添加 AI 模型支持

编辑 `app/services/ai_service.py`，主要涉及：
- `_call_text()` - 文本补全
- `_call_vision()` - 多模态图文分析
- `_call_vlm()` - MiniMax 等专用 VLM 端点

---

## 许可证

MIT License

---

## 致谢

- [Flask](https://flask.palletsprojects.com/) - 轻量级 Python Web 框架
- [Bootstrap](https://getbootstrap.com/) - 前端 UI 框架
- [OpenAI](https://openai.com/) - AI API
