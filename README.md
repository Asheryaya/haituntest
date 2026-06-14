# 海豚计划四期人才测评系统

## 系统简介

本系统是为"海豚计划四期"人才测评项目开发的在线测评平台，支持：

- **DISC行为风格测试**（40题）：识别用户的行为风格特征
- **情景模拟测评**（8题）：基于真实业务场景的决策能力评估
- **培训需求调研**（2题）：收集用户的培训需求和期望

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动系统

```bash
python run.py
```

系统将自动：
- 初始化数据库
- 创建管理员账户（如不存在）
- 启动Web服务器

### 3. 访问系统

打开浏览器访问：**http://localhost:5000**

## 默认账户

### 管理员账户
- 用户名：`admin`
- 密码：`admin123`

### 普通用户
- 访问注册页面创建新账户

## 功能说明

### 普通用户功能

1. **我的测评**
   - 查看测评状态（未开始/进行中/已完成）
   - 开始或继续测评

2. **DISC行为风格测试**
   - 40道单选题
   - 自动计算D/I/S/C四种类型得分
   - 生成详细的行为风格分析报告

3. **情景模拟测评**
   - 8道情景题
   - 基于卓力真实业务场景设计
   - 评估决策思维和管理能力

4. **培训需求调研**
   - 2道开放性问题
   - 收集工作亮点和学习期待

### 管理员功能

1. **管理后台**
   - 数据概览和统计
   - 各部分完成率
   - DISC类型分布

2. **用户管理**
   - 查看所有用户列表
   - 删除用户
   - 导出用户列表

3. **测评结果**
   - 查看所有用户的测评结果
   - 按类型筛选
   - 查看DISC详细报告

4. **数据导出**
   - 导出用户列表（Excel）
   - 导出DISC测评结果（Excel）
   - 导出情景测评结果（Excel）
   - 导出培训需求调研（Excel）

## 项目结构

```
assessment_system/
├── app.py              # Flask主应用
├── config.py           # 配置文件
├── models.py           # 数据库模型
├── init_db.py          # 数据库初始化脚本
├── run.py              # 启动脚本
├── requirements.txt    # 依赖包
├── utils/
│   ├── scoring.py      # DISC评分算法
│   └── export.py       # Excel导出功能
├── static/
│   ├── css/
│   │   └── style.css   # 样式文件
│   └── js/
│       └── main.js     # 前端交互
└── templates/
    ├── base.html        # 基础模板
    ├── login.html       # 登录页面
    ├── register.html    # 注册页面
    ├── dashboard.html   # 用户仪表盘
    ├── disc_test.html   # DISC测试页面
    ├── scenario_test.html # 情景测评页面
    ├── survey.html      # 培训需求调研
    ├── result.html      # 测评结果页面
    └── admin/
        ├── dashboard.html # 管理后台
        ├── users.html     # 用户管理
        └── results.html   # 测评结果
```

## 技术栈

- **后端**：Python Flask
- **数据库**：SQLite
- **前端**：HTML + CSS + JavaScript
- **依赖**：Flask-Login, Flask-SQLAlchemy, openpyxl

## 注意事项

1. 首次运行会自动创建数据库和管理员账户
2. 数据存储在 `instance/assessment.db` 文件中
3. 如需重置系统，删除 `instance/` 目录即可
4. 生产环境请修改 `config.py` 中的 `SECRET_KEY`

## 联系方式

海豚计划项目组 © 2026
