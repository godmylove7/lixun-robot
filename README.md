# Lixun Robot - 知识库驱动的聊天机器人

基于向量检索和LLM的智能聊天机器人，支持多轮对话和文档知识库。

## 功能特性

- 📁 支持 PDF、Word、TXT、Markdown 文档上传
- 🔍 基于向量检索的智能问答
- 💬 多轮对话上下文管理
- 📊 LangSmith 调用链可观测性
- 🐳 Docker 容器化部署

## 技术栈

- **LLM**: 通义千问 (DashScope)
- **框架**: LangChain + LangGraph + FastAPI
- **向量库**: FAISS
- **监控**: LangSmith

## 快速开始

### 1. 安装依赖

```bash
# 使用 uv 安装依赖
uv sync