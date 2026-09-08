from sentence_transformers import SentenceTransformer


MODEL_NAME = "BAAI/bge-small-zh-v1.5"

model = SentenceTransformer(MODEL_NAME)


def encode_text(text: str):
    """
    将文本转换为 Embedding 向量
    """
    vector = model.encode(
        text,
        normalize_embeddings=True
    )

    return vector.tolist()