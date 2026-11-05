from pathlib import Path
import shutil
import logging
import re
import time
import unicodedata

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from rag import ensure_dirs, load_index, add_pdf, search, UPLOAD_DIR, EMBEDDING_MODEL

BASE_DIR = Path(__file__).resolve().parent
FRONTEND = BASE_DIR.parent / "index.html"

app = FastAPI(title="AI知识复用助手 · RAG Spike V0.1 Local")
logger = logging.getLogger("rag.connect")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
ensure_dirs()

@app.middleware("http")
async def request_timing(request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    if request.url.path in ("/api/connect", "/api/associate"):
        response.headers["X-Process-Ms"] = str(round((time.perf_counter()-start)*1000))
    return response

class SearchRequest(BaseModel):
    query: str
    top_k: int = 5

@app.get("/")
def home():
    return FileResponse(FRONTEND)

@app.get("/api/health")
def health():
    return {"ok": True, "embedding": "local", "model": EMBEDDING_MODEL}

@app.get("/api/assets")
def assets():
    return {"assets": load_index().get("assets", [])}

@app.post("/api/upload")
async def upload(file: UploadFile = File(...)):
    filename = Path(file.filename or "").name
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="V0.1 目前只支持 PDF。")
    target = UPLOAD_DIR / filename
    with target.open("wb") as f:
        shutil.copyfileobj(file.file, f)
    try:
        return add_pdf(filename, target)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"PDF 处理失败：{e}")

@app.post("/api/search")
def semantic_search(req: SearchRequest):
    query = req.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="搜索内容不能为空。")
    try:
        results = search(query, max(1, min(req.top_k, 10)))
        return {"query": query, "results": results, "retrieval": "local_semantic_embedding", "model": EMBEDDING_MODEL}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"检索失败：{e}")


class ConnectRequest(BaseModel):
    query: str
    context: str | dict | None = None


def safe_upstream_error_message(error: Exception) -> str:
    """Extract a short, redacted diagnostic message without logging request data."""
    body = getattr(error, "body", None)
    if isinstance(body, dict):
        upstream_error = body.get("error", body)
        if isinstance(upstream_error, dict):
            message = upstream_error.get("message") or upstream_error.get("code") or "upstream error"
        else:
            message = str(upstream_error)
    else:
        message = str(error)

    message = re.sub(r"(?i)(api[_-]?key|authorization)\s*[:=]\s*\S+", r"\1=[REDACTED]", message)
    message = re.sub(r"\bsk-[A-Za-z0-9_-]+\b", "[REDACTED]", message)
    return message[:500]

@app.post("/api/connect")
def connect(req: ConnectRequest):
    try:
        from generation import explain
        if not req.query.strip():
            raise ValueError("缺少用户记忆描述")
        context = req.context
        if isinstance(context, dict):
            context = context.get("original") or context.get("text") or str(context)
        context = context or ""
        if not context.strip():
            raise ValueError("未收到检索片段")
        result = explain(req.query, context)
        return {"explanation": result}
    except Exception as e:
        logger.error(
            "connect_generation_failed type=%s upstream_status=%s upstream_message=%s",
            type(e).__name__,
            getattr(e, "status_code", None),
            safe_upstream_error_message(e),
        )
        raise HTTPException(status_code=500, detail="AI 理解服务暂时不可用。")


class AssociationRequest(BaseModel):
    problem: str
    context: str


class AuthorMethod(BaseModel):
    method: str
    evidence: str
    conditions: str


class AssociationResult(BaseModel):
    relation: str
    sufficient: bool
    author_method: AuthorMethod | None
    ai_suggestion: str | None


def original_evidence(evidence, context):
    if evidence in context:
        return evidence
    def canonical(text):
        chars, positions = [], []
        for index, char in enumerate(text):
            for normalized in unicodedata.normalize('NFKC', char):
                if not normalized.isspace():
                    chars.append(normalized)
                    positions.append(index)
        return ''.join(chars), positions
    needle, _ = canonical(evidence)
    haystack, positions = canonical(context)
    start = haystack.find(needle) if needle else -1
    if start < 0:
        raise ValueError('evidence_not_in_passage')
    return context[positions[start]:positions[start+len(needle)-1]+1]


def validate_association(raw, context):
    result = AssociationResult.model_validate(raw, strict=True)
    if not result.relation.strip() or result.relation.strip() == "关联分析与适用边界":
        raise ValueError("relation_missing_or_placeholder")
    if not result.sufficient and (result.author_method or result.ai_suggestion):
        raise ValueError("action_without_evidence")
    if result.author_method:
        method = result.author_method
        if not all(value.strip() for value in (method.method, method.evidence, method.conditions)):
            raise ValueError("author_fields_empty")
        if result.ai_suggestion is not None:
            raise ValueError("conflicting_action_types")
        method.evidence = original_evidence(method.evidence, context)
    if result.ai_suggestion is not None and not result.ai_suggestion.strip():
        raise ValueError("suggestion_empty")
    return result


@app.post("/api/associate", response_model=AssociationResult)
def association(req: AssociationRequest):
    if not req.problem.strip() or not req.context.strip():
        raise HTTPException(status_code=400, detail="请提供当前问题和已确认片段。")
    stage = 'model_or_parse'
    try:
        from generation import associate
        raw = associate(req.problem.strip(), req.context)
        stage = 'schema_or_evidence'
        return validate_association(raw, req.context)
    except Exception as error:
        # Do not expose upstream messages, request contents or credentials.
        safe_codes = {'relation_missing_or_placeholder', 'action_without_evidence', 'author_fields_empty', 'conflicting_action_types', 'evidence_not_in_passage', 'suggestion_empty'}
        reason = str(error) if type(error) is ValueError and str(error) in safe_codes else 'not_logged'
        logger.error("association_failed stage=%s type=%s reason=%s status=%s", getattr(error, 'stage', stage), type(error).__name__, reason, getattr(error, "status_code", None))
        raise HTTPException(status_code=502, detail="关联分析暂时不可用，请重试；当前片段已保留。")


if __name__ == "__main__":
    print("Registered routes:", [r.path for r in app.routes])
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
