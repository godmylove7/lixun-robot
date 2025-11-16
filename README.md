Lixun Robot - 知识库驱动的聊天机器人

基于向量检索和LLM的智能聊天机器人，支持多轮对话和文档知识库。
功能特性

    📁 支持 PDF、Word、TXT、Markdown 文档上传

    🔍 基于向量检索的智能问答

    💬 多轮对话上下文管理

    📊 LangSmith 调用链可观测性

    🐳 Docker 容器化部署

技术栈

    LLM: 通义千问 (DashScope)

    框架: LangChain + LangGraph + FastAPI

    向量库: FAISS

    监控: LangSmith

快速开始
1. 安装依赖
bash

# 使用 uv 安装依赖
uv sync

2. 设置环境变量
bash

# 复制环境模板文件
copy .env.example .env

# 编辑 .env 文件，填写 API 密钥

3. 启动应用
bash

# 运行环境检查
python scripts/check_env.py

# 启动机器人
python scripts/start.py

🐳 Docker 部署
使用 Docker Compose
bash

# 一键启动
docker-compose up --build

# 后台运行
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down

使用 Docker
bash

# 构建镜像
docker build -t lixun-robot .

# 运行容器
docker run -it --env-file .env lixun-robot

🛠️ 开发

详细开发指南请参阅 CONTRIBUTING.md
项目结构
text

lixun-robot/
├── chains/              # 聊天代理和工作流
├── core/                # 核心组件
├── scripts/             # 工具脚本
├── data/                # 数据存储
├── .github/workflows/   # CI/CD配置
├── Dockerfile           # Docker配置
├── docker-compose.yml   # 容器编排
├── pyproject.toml       # 项目配置
└── run.py              # 主程序入口

🤝 贡献

欢迎提交 Issue 和 Pull Request！
📄 许可证

MIT License