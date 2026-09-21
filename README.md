# Project 01｜RAG Spike V0.1｜Local Embedding

这一版把 Embedding 改成**完全在本机运行**，不需要 OpenAI API Key，也不需要 API 充值。

## 核心闭环

PDF → 文本解析 → Chunk → 本地 Embedding → 本地向量索引 → Semantic Retrieval → V1.5 Results

使用的中文 Embedding 模型是 `BAAI/bge-small-zh-v1.5`。FastEmbed 官方模型列表显示该模型约 0.09 GB；FastEmbed 使用 ONNX Runtime 在本机生成向量。第一次使用会下载模型，之后复用本地缓存。

## 你只需要做

### 1. 安装/更新依赖

在 `backend` 文件夹打开 PowerShell：

```powershell
python -m pip install -r requirements.txt
```

### 2. 启动

```powershell
python server.py
```

看到：

```text
Uvicorn running on http://127.0.0.1:8000
```

浏览器打开 `http://127.0.0.1:8000`。

### 3. 第一次上传 PDF

第一次点击“选择 PDF”时，程序可能先下载约 90 MB 的本地中文 Embedding 模型。这是正常的。下载完成后才会建立 PDF 索引。

## 当前限制

- 只支持文字型 PDF，不支持纯扫描 PDF OCR。
- 向量索引保存在本机。
- 暂未接真实 LLM Generation；Connect / Follow-up 仍沿用原 Demo 模拟逻辑。
- 当前目标是验证 Retrieval，不等于已经验证完整产品假设。


## Retrieval 阈值（实验设置）

当前暂设语义相似度阈值为 **0.55**。

这不是经过大规模验证的“正确答案阈值”，只是当前 Spike 用来避免明显无关输入被强行返回的实验参数。后续应通过更多正例 / 负例测试调整。

当最高候选低于该阈值时，产品会显示“暂时没有找到足够可靠的匹配”，并引导用户补充记忆线索。


## Generation Spike
已加入 DeepSeek Generation 接口 /api/connect。API Key 请通过环境变量 DEEPSEEK_API_KEY 提供。
