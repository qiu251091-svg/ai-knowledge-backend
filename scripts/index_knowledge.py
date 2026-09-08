from pathlib import Path
from uuid import uuid4

from qdrant_client.models import (
    PointStruct,
    Distance,
    VectorParams,
    Filter,
    FieldCondition,
    MatchValue,
    FilterSelector,
)

from app.services.embedding_service import encode_text
from app.services.qdrant_service import (
    client,
    COLLECTION_NAME,
)

KB = Path("data/knowledge.txt")
KB_SOURCE = str(KB)


def chunks(text: str):
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    return [
        block.strip()
        for block in text.split("\n\n")
        if block.strip()
    ]


def index_knowledge():
    if not KB.exists():
        raise FileNotFoundError(
            f"Knowledge file not found: {KB}"
        )

    # 1. 检查 collection 是否存在
    collections = client.get_collections().collections

    exists = any(
        collection.name == COLLECTION_NAME
        for collection in collections
    )

    # 2. 不存在才创建
    if not exists:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=512,
                distance=Distance.COSINE,
            ),
        )

        print(f"Collection '{COLLECTION_NAME}' created.")

    else:
        print(f"Collection '{COLLECTION_NAME}' already exists.")

        # 3. 只删除 knowledge.txt 对应的旧向量
        client.delete(
            collection_name=COLLECTION_NAME,
            points_selector=FilterSelector(
                filter=Filter(
                    must=[
                        FieldCondition(
                            key="source",
                            match=MatchValue(
                                value=KB_SOURCE
                            ),
                        )
                    ]
                )
            ),
        )

        print(
            f"Old vectors from '{KB_SOURCE}' deleted."
        )

    # 4. 读取基础知识库
    text = KB.read_text(encoding="utf-8")
    text_chunks = chunks(text)

    if not text_chunks:
        print("No knowledge chunks found.")
        return

    # 5. 重新向量化
    points = []

    for index, chunk in enumerate(text_chunks):
        vector = encode_text(chunk)

        point = PointStruct(
            id=str(uuid4()),
            vector=vector,
            payload={
                "text": chunk,
                "source": KB_SOURCE,
                "chunk_index": index,
            },
        )

        points.append(point)

    # 6. 写入 Qdrant
    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points,
    )

    print(f"Indexed {len(points)} chunks.")


if __name__ == "__main__":
    index_knowledge()