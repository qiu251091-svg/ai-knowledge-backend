from io import BytesIO
from pypdf import PdfReader
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, UploadFile, File, HTTPException
from qdrant_client.models import (
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    FilterSelector,
)
from app.services.embedding_service import encode_text
from app.services.qdrant_service import client, COLLECTION_NAME


router = APIRouter()

UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".txt", ".md", ".pdf"}


def split_text(
    text: str,
    chunk_size: int = 500,
    overlap: int = 100
):
    # 统一换行符
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.strip()

    if not text:
        return []

    chunks = []
    start = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break

        # 下一个 chunk 向前重叠 100 个字符
        start = end - overlap

    return chunks


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...)
):
    filename = file.filename or ""
    suffix = Path(filename).suffix.lower()

    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Only txt, md and pdf files are supported."
        )

    save_path = UPLOAD_DIR / filename

    content = await file.read()

    # 保存原始文件
    with open(save_path, "wb") as f:
        f.write(content)

    chunks = []

    if suffix in {".txt", ".md"}:
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            raise HTTPException(
                status_code=400,
                detail="File encoding must be UTF-8."
            )

        chunks = split_text(text)

    elif suffix == ".pdf":
        try:
            reader = PdfReader(BytesIO(content))

            pages = []

            for page in reader.pages:
                page_text = page.extract_text()

                if page_text:
                    pages.append(page_text.strip())

            text = "\n\n".join(pages)
            chunks = split_text(text)

        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to parse PDF: {str(e)}"
            )

    if not chunks:
        raise HTTPException(
            status_code=400,
            detail="No text content could be extracted."
        )

    # 每个 chunk 做 Embedding
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

    # 删除这个文件以前的向量，避免重复索引
    client.delete(
        collection_name=COLLECTION_NAME,
        points_selector=FilterSelector(
            filter=Filter(
                must=[
                    FieldCondition(
                        key="source",
                        match=MatchValue(value=filename),
                    )
                ]
            )
        ),
    )
    # 写入 Qdrant
    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points,
    )

    return {
        "message": "Document uploaded and indexed successfully",
        "filename": filename,
        "chunk_count": len(chunks),
        "indexed_count": len(points),
    }
@router.get("")
def list_documents():
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
            source = payload.get("source")

            if source:
                documents.add(source)

        if next_offset is None:
            break

        offset = next_offset

    return {
        "documents": sorted(documents),
        "total": len(documents),
    }
@router.delete("/{filename}")
def delete_document(filename: str):
    # 删除 Qdrant 中该文档对应的所有向量
    client.delete(
        collection_name=COLLECTION_NAME,
        points_selector=FilterSelector(
            filter=Filter(
                must=[
                    FieldCondition(
                        key="source",
                        match=MatchValue(value=filename),
                    )
                ]
            )
        ),
    )

    # 删除本地上传文件
    file_path = UPLOAD_DIR / filename

    if file_path.exists():
        file_path.unlink()

    return {
        "message": "Document deleted successfully",
        "filename": filename,
    }