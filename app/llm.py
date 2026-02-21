import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("HUGGINGFACE_API_KEY")

if not api_key:
    raise ValueError("HUGGINGFACE_API_KEY not found in .env")

client = OpenAI(
    api_key=api_key,
    base_url="https://router.huggingface.co/v1"
)

def ask_llm(question: str):
    response = client.chat.completions.create(
        model="mistralai/Mistral-7B-Instruct-v0.2",
        messages=[
            {"role": "system", "content": "You are a helpful AI assistant."},
            {"role": "user", "content": question}
        ],
        temperature=0.7,
    )

    return response.choices[0].message.content
