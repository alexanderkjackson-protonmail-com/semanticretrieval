from openai import OpenAI
from pymilvus import MilvusClient

MODEL_NAME = "text-embedding-3-small"
COLLECTION_NAME = "demo_collection"
TOP_K = 3  # Number of nearest matches to return

# Load OpenAI API key from file
with open("openai_key.txt", "r") as f:
    api_key = f.read().strip()

# Set up OpenAI and Milvus clients
openai_client = OpenAI(api_key=api_key)
milvus_client = MilvusClient(host="localhost", port=19530)

# Interactive search loop
while True:
    query = input("Search query (or 'exit'): ").strip()
    if query.lower() == "exit":
        break

    # Get embedding
    query_embedding = openai_client.embeddings.create(
        input=[query],
        model=MODEL_NAME
    ).data[0].embedding

    # Search Milvus
    results = milvus_client.search(
        collection_name=COLLECTION_NAME,
        data=[query_embedding],
        limit=TOP_K,
        output_fields=["text", "subject"]
    )

    print("\nTop results:")
    for hit in results[0]:  # Each hit is a Hit object
        text = hit.entity.get("text", "[No text]")
        subject = hit.entity.get("subject", "[No subject]")
        score = hit.distance
        print(f"- Text: {text}\n  Subject: {subject}\n  Score: {score:.4f}\n")
