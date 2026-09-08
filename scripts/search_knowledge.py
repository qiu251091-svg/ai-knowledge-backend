from app.services.embedding_service import encode_text
from app.services.qdrant_service import (
    client,
    COLLECTION_NAME,
)


def search(question: str, top_k: int = 3):

    query_vector = encode_text(question)

    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=top_k,
        with_payload=True,
    ).points

    print("\n========== SEARCH RESULT ==========")

    for i, result in enumerate(results, start=1):

        print(f"\n--- Result {i} ---")
        print("Score:", result.score)
        print("Text:")
        print(result.payload.get("text"))
        print("Source:")
        print(result.payload.get("source"))


if __name__ == "__main__":

    question = input("请输入问题：")

    search(question)