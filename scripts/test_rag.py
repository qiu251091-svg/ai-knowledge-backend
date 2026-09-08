from app.services.rag_service import answer_question


if __name__ == "__main__":

    question = input("请输入问题：")

    answer, sources = answer_question(question)

    print("\n========== RAG RESULT ==========")

    print("\nAnswer:")
    print(answer)

    print("\nSources:")
    print(sources)