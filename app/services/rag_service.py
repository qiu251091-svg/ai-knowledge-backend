from app.services.embedding_service import encode_text
from app.services.qdrant_service import (
    client,
    COLLECTION_NAME,
)
from app.services.llm_service import generate_answer


def answer_question(question: str, top_k: int = 2):
    query_vector = encode_text(question)

    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=top_k,
        with_payload=True,
    ).points

    if not results:
        return "知识库中暂时没有相关内容。", []

    context_list = []
    sources = []

    for result in results:
        payload = result.payload or {}

        text = payload.get("text")
        if text:
            context_list.append(text)

        source = payload.get("source")
        if source and source not in sources:
            sources.append(source)

    if not context_list:
        return "知识库中暂时没有相关内容。", []

    context = "\n\n".join(context_list)

    answer = generate_answer(
        question=question,
        context=context,
    )

    return answer, sources