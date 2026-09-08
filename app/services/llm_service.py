import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

API_KEY = os.getenv("DASHSCOPE_API_KEY")
BASE_URL = os.getenv("LLM_BASE_URL")
MODEL = os.getenv("LLM_MODEL", "qwen-plus")

if not API_KEY:
    raise RuntimeError("DASHSCOPE_API_KEY is not configured")

client = OpenAI(
    api_key=API_KEY,
    base_url=BASE_URL,
)


def generate_answer(question: str, context: str) -> str:
    prompt = f"""
请根据下面的知识库内容回答用户的问题。

要求：
1. 主要依据知识库内容回答。
2. 不要编造知识库中不存在的信息。
3. 使用简洁、自然的中文。
4. 如果知识库无法回答，请明确说明。

知识库内容：
{context}

用户问题：
{question}
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": "你是一个基于知识库回答问题的中文AI助手。"
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.3,
    )

    return response.choices[0].message.content