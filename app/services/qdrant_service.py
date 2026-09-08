import os

from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

load_dotenv()

QDRANT_URL = os.getenv(
    "QDRANT_URL",
    "http://localhost:6333"
)

COLLECTION_NAME = "knowledge_base"

client = QdrantClient(url=QDRANT_URL)


def create_collection():
    """
    创建知识库向量集合
    """

    collections = client.get_collections().collections

    exists = any(
        collection.name == COLLECTION_NAME
        for collection in collections
    )

    if not exists:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=512,
                distance=Distance.COSINE,
            ),
        )

        print(
            f"Collection '{COLLECTION_NAME}' created."
        )

    else:
        print(
            f"Collection '{COLLECTION_NAME}' already exists."
        )