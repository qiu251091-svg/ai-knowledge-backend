import re
from io import BytesIO
from pathlib import Path
from uuid import uuid4

from fastapi import (
    APIRouter,
    UploadFile,
    File,
    HTTPException,
    Depends,
)
from pypdf import PdfReader
from qdrant_client.models import (
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    FilterSelector,
)

from app.services.auth_service import require_user
from app.services.embedding_service import encode_text
from app.services.qdrant_service import client, COLLECTION_NAME
from app.redis_client import redis_client


router = APIRouter()

# ==============================
# 上传目录
# ==============================

UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# ==============================
# 文件配置
# ==============================

ALLOWED_EXTENSIONS = {
    ".txt",
    ".md",
    ".pdf",
}

# 支持：
# 英文
# 数字
# 中文
# 下划线
# 横线
# 空格
# 括号
# 点号
SAFE_FILENAME_PATTERN = re.compile(
    r"^[\w\-. ()\u4e00-\u9fff]+$"
)


# ==============================
# 文件名安全检查
# ==============================

def validate_filename(filename: str) -> str:
    """
    Validate uploaded/deleted filenames and prevent path traversal.
    """

    if not filename:
        raise HTTPException(
            status_code=400,
            detail="Invalid filename.",
        )

    # Path(filename).name 会移除目录部分
    safe_filename = Path(filename).name

    # 如果原始文件名包含路径，例如：
    # ../../test.txt
    # 则直接拒绝，而不是静默转换
    if safe_filename != filename:
        raise HTTPException(
            status_code=400,
            detail="Invalid filename path.",
        )

    if not SAFE_FILENAME_PATTERN.fullmatch(safe_filename):
        raise HTTPException(
            status_code=400,
            detail="Filename contains invalid characters.",
        )

    suffix = Path(safe_filename).suffix.lower()

    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Only txt, md and pdf files are supported.",
        )

    return safe_filename


# ==============================
# Redis 缓存失效
# ==============================

def clear_chat_cache():
    """
    Clear cached RAG answers after the knowledge base changes.
    """

    keys = redis_client.scan_iter(
        match="chat:*"
    )

    for key in keys:
        redis_client.delete(key)


# ==============================
# 文本切块
# ==============================

def split_text(
    text: str,
    chunk_size: int = 500,
    overlap: int = 100,
):
    """
    Split text into overlapping chunks.
    """

    # 统一换行符
    text = text.replace(
        "\r\n",
        "\n",
    ).replace(
        "\r",
        "\n",
    )

    text = text.strip()

    if not text:
        return []

    chunks = []

    start = 0

    while start < len(text):
        end = min(
            start + chunk_size,
            len(text),
        )

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break

        # 下一个 chunk 与当前 chunk 重叠
        start = end - overlap

    return chunks


# ==============================
# 上传文档
# ==============================

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    _username: str = Depends(require_user),
):
    """
    Upload and index a document into Qdrant.
    JWT authentication is required.
    """

    # ==========================
    # 1. 文件名安全校验
    # ==========================

    filename = validate_filename(
        file.filename or ""
    )

    suffix = Path(filename).suffix.lower()

    save_path = UPLOAD_DIR / filename

    # ==========================
    # 2. 读取文件
    # ==========================

    content = await file.read()

    if not content:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty.",
        )

    # ==========================
    # 3. 提取文本
    # ==========================

    if suffix in {
        ".txt",
        ".md",
    }:
        try:
            text = content.decode(
                "utf-8"
            )

        except UnicodeDecodeError:
            raise HTTPException(
                status_code=400,
                detail="File encoding must be UTF-8.",
            )

    elif suffix == ".pdf":
        try:
            reader = PdfReader(
                BytesIO(content)
            )

            pages = []

            for page in reader.pages:
                page_text = page.extract_text()

                if page_text:
                    pages.append(
                        page_text.strip()
                    )

            text = "\n\n".join(pages)

        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to parse PDF: {str(e)}",
            )

    else:
        # 理论上不会执行到这里
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type.",
        )

    # ==========================
    # 4. 文本切块
    # ==========================

    chunks = split_text(text)

    if not chunks:
        raise HTTPException(
            status_code=400,
            detail="No text content could be extracted.",
        )

    # ==========================
    # 5. Embedding
    # ==========================

    points = []

    for index, chunk in enumerate(chunks):

        vector = encode_text(chunk)

        point = PointStruct(
            id=str(uuid4()),
            vector=vector,
            payload={
                "text": chunk,
                "source": filename,
                "chunk_index": index,
            },
        )

        points.append(point)

    # ==========================
    # 6. 删除同名旧向量
    # ==========================

    client.delete(
        collection_name=COLLECTION_NAME,
        points_selector=FilterSelector(
            filter=Filter(
                must=[
                    FieldCondition(
                        key="source",
                        match=MatchValue(
                            value=filename
                        ),
                    )
                ]
            )
        ),
    )

    # ==========================
    # 7. 写入新向量
    # ==========================

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points,
    )

    # ==========================
    # 8. 保存原始文件
    # ==========================

    try:
        with open(
            save_path,
            "wb",
        ) as f:
            f.write(content)

    except OSError:
        raise HTTPException(
            status_code=500,
            detail="Failed to save uploaded file.",
        )

    # ==========================
    # 9. 清除旧 RAG 缓存
    # ==========================

    clear_chat_cache()

    return {
        "message": "Document uploaded and indexed successfully",
        "filename": filename,
        "chunk_count": len(chunks),
        "indexed_count": len(points),
    }


# ==============================
# 查询文档列表
# ==============================

@router.get("")
def list_documents(
    _username: str = Depends(require_user),
):
    """
    List documents currently indexed in Qdrant.
    JWT authentication is required.
    """

    documents = set()

    offset = None

    while True:
        records, next_offset = client.scroll(
            collection_name=COLLECTION_NAME,
            limit=100,
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )

        for record in records:
            payload = record.payload or {}

            source = payload.get(
                "source"
            )

            if source:
                documents.add(source)

        if next_offset is None:
            break

        offset = next_offset

    return {
        "documents": sorted(documents),
        "total": len(documents),
    }


# ==============================
# 删除文档
# ==============================

@router.delete("/{filename}")
def delete_document(
    filename: str,
    _username: str = Depends(require_user),
):
    """
    Delete a document and its Qdrant vectors.
    JWT authentication is required.
    """

    # ==========================
    # 1. 文件名安全校验
    # ==========================

    filename = validate_filename(
        filename
    )

    # ==========================
    # 2. 删除 Qdrant 向量
    # ==========================

    client.delete(
        collection_name=COLLECTION_NAME,
        points_selector=FilterSelector(
            filter=Filter(
                must=[
                    FieldCondition(
                        key="source",
                        match=MatchValue(
                            value=filename
                        ),
                    )
                ]
            )
        ),
    )

    # ==========================
    # 3. 删除本地文件
    # ==========================

    file_path = UPLOAD_DIR / filename

    if file_path.exists():
        try:
            file_path.unlink()

        except OSError:
            raise HTTPException(
                status_code=500,
                detail="Failed to delete local file.",
            )

    # ==========================
    # 4. 清除旧 RAG 缓存
    # ==========================

    clear_chat_cache()

    return {
        "message": "Document deleted successfully",
        "filename": filename,
    }