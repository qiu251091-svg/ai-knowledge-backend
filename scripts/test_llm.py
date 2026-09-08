from app.services.llm_service import generate_answer


if __name__ == "__main__":
    question = "什么是RAG？"

    context = """
RAG 是 Retrieval-Augmented Generation，
即检索增强生成。它会先从知识库检索相关内容，
然后把检索结果交给大语言模型生成回答。
"""

    answer = generate_answer(question, context)

    print("\n========== LLM RESULT ==========")
    print(answer)