贡献指南
开发环境设置
1. 克隆项目
bash

git clone https://github.com/godmylove7/lixun-robot.git
cd lixun-robot

2. 设置环境变量
bash

# Windows
copy .env.example .env

# Linux/Mac
cp .env.example .env

# 编辑 .env 文件，填写你的 DashScope API 密钥

3. 安装依赖
bash

# 使用 uv 安装依赖
uv sync

4. 运行环境检查
bash

python scripts/check_env.py

5. 启动应用
bash

# 方式一：使用启动脚本（推荐）
python scripts/start.py

# 方式二：直接运行
uv run python run.py

开发规范
分支管理

    main - 主分支，稳定版本

    develop - 开发分支

    feature/* - 功能分支

    fix/* - 修复分支

提交信息规范

使用 Conventional Commits 格式：

    feat: 新功能

    fix: 修复bug

    docs: 文档更新

    style: 代码格式

    refactor: 重构

    test: 测试

Pull Request 流程

    从 develop 创建功能分支

    开发完成后提交 PR

    通过代码审查后合并

测试
bash

# 运行环境检查测试
python scripts/check_env.py

# 确保所有模块可以正常导入
python -c "from chains.chat_agent import ChatAgent; print('导入成功')"