# AI Knowledge Reuse Assistant

> 找回那些“我记得看过，但想不起在哪里”的知识。

一个面向个人知识资产的 AI 知识复用助手。

用户可以用自然语言描述当前想解决的问题或记忆线索，从自己的阅读资料中找到相关内容，并进一步理解这些内容为什么与当前问题有关。

**Portfolio Project · AI Product / RAG Prototype**

---

## 01｜Why

信息记录并不等于知识复用。

人在阅读过程中会积累大量书籍、文章、笔记和摘录，但当真正遇到问题时，往往只记得：

> “我好像在哪里看过这个观点。”

却很难再次找到它，更难判断它是否真的能帮助当前的问题。

因此，这个项目尝试解决的是：

**如何让用户以“记忆中的问题、观点或场景”重新找到过去接触过的知识，并把它连接到当前问题。**

---

## 02｜Core Product Flow

### Find → Understand → Connect

### ① Find｜找回

用户不需要准确记得关键词，而是用自然语言描述自己想找回的内容。

系统通过 **Semantic Retrieval（语义检索）**，从个人知识资产中寻找相关内容。

### ② Understand｜理解

AI 对检索到的内容进行辅助解释，帮助用户判断：

- 哪些内容与当前问题有关
- 这种关联是直接匹配、主题相近，还是仅提供背景参考
- 当前证据是否足够

### ③ Connect｜关联与继续使用

用户确认相关内容后，再决定是否将其用于当前问题。

> **AI 提供候选与解释，但最终判断仍由用户完成。**

---

## 03｜Product Prototype

当前 Demo 的核心体验：

**自然语言描述 → Semantic Retrieval → 检索结果 → AI 辅助解释**

当前版本重点验证的是核心交互与 Retrieval 能力，而不是完整的知识管理系统。

---

## 04｜What I Built

这个项目由我独立完成产品设计、Prototype、Web Demo 与 RAG Spike 验证。

### Product

- 定义核心用户问题与使用场景
- 设计 `Find → Understand → Connect` 核心产品 Flow
- 明确 MVP / MLP 边界，聚焦“知识找回与复用”
- 设计 AI 的介入边界：辅助用户判断，而不是替代用户判断

### Prototype & Validation

- 完成 Figma Prototype
- 完成可运行的 Web Demo
- 使用真实 PDF 材料进行 Retrieval 测试
- 观察并记录 Retrieval Relevance 与 AI Explanation 中的问题
- 根据实际测试结果调整验证边界

### AI / Technical Exploration

实现并验证了一条完整的 RAG Prototype Pipeline：

**PDF → Text Parsing → Chunking → Local Embedding → Semantic Retrieval → LLM-assisted Explanation**

---

## 05｜Technical Overview

### Retrieval Pipeline

```text
PDF
 ↓
Text Parsing
 ↓
Chunking
 ↓
Local Embedding
 ↓
Semantic Retrieval
 ↓
LLM-assisted Relevance Explanation
Core Stack
Frontend: HTML / CSS / JavaScript
Backend: FastAPI
Embedding: BAAI/bge-small-zh-v1.5
Vector Retrieval: Local semantic similarity search
LLM: DeepSeek API
PDF Parsing: pypdf
Retrieval Settings

当前 Prototype 使用：

Chunk size：700 characters
Chunk overlap：120 characters
Similarity threshold：0.55
Top-K retrieval：5

0.55 是当前 Spike 的实验参数，并不是经过大规模验证后的“正确阈值”。

06｜Current Status
Capability	Status
PDF parsing	✅
Text chunking	✅
Local embedding	✅
Semantic retrieval	✅
LLM-assisted relevance explanation	✅
Web Demo	✅
Production deployment	—

当前版本用于验证核心产品 Flow 与 RAG Retrieval 能力。

07｜Known Limitations

当前 Prototype 仍存在一些明确限制：

目前主要支持文字型 PDF，不包含 OCR 能力。
Retrieval quality 仍受到 Chunking 与 Similarity Threshold 的影响。
当前知识资产与向量索引主要用于本地 Demo / Spike 验证。
尚未进行大规模用户测试，因此目前无法判断长期使用价值。
当前重点是验证核心交互与 AI 能力边界，而不是构建完整的知识管理系统。
08｜Product Judgment

这个项目并不是为了证明“RAG 可以工作”。

更重要的问题是：

什么环节真正需要 AI？什么环节应该继续由用户判断？

在这个 Prototype 中，我将 AI 的角色限制在：

检索候选 + 解释关联

而不是：

替用户判断“这个知识一定有用”。

因此，当检索证据不足时，系统应该允许结果停留在：

目前无法判断。

而不是为了生成一个看起来合理的答案，强行建立关联。

09｜Local Development
Requirements
Python 3.10+
FastAPI
Uvicorn
FastEmbed
pypdf
DeepSeek API Key（用于 AI Explanation）
Install Dependencies

进入 backend 目录：

python -m pip install -r requirements.txt
Start

在项目根目录运行：

start-rag.bat

或者进入 backend 后运行：

python server.py

启动后访问：

http://127.0.0.1:8000

首次使用 Local Embedding 时，程序可能需要下载约 90 MB 的模型文件。

Environment Variable

LLM Explanation 使用 DeepSeek API。

请通过环境变量提供：

DEEPSEEK_API_KEY

API Key 不应写入代码或提交到 GitHub。

10｜Reflection

这个项目让我进一步确认：

AI Product 的重点不只是“把 AI 接进产品”，而是判断 AI 应该在哪里介入，以及它应该承担什么程度的决策责任。

在这个项目中，我最终将核心体验收敛为：

Find → Understand → Connect

而不是继续扩展成一个完整的知识管理系统。

对于当前阶段，我更关注：

问题是否成立 → AI 是否真的降低了完成成本 → 用户是否仍然保留判断权 → 哪些假设还需要进一步验证。

Project Scope

This repository represents a working AI Product / RAG Prototype for portfolio and interview demonstration.

It is not intended to represent a production-ready knowledge management system.


---
