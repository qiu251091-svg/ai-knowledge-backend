from sentence_transformers import SentenceTransformer

print("正在加载 Embedding 模型...")

model = SentenceTransformer("BAAI/bge-small-zh-v1.5")

text = "RAG 是一种检索增强生成技术。"

vector = model.encode(text)

print("Embedding successful!")
print("Vector dimension:", len(vector))
print("Vector type:", type(vector))