"""
直接测试 SiliconFlow API - 使用配置文件的值
"""
import asyncio
from openai import AsyncOpenAI
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("SILICONFLOW_API_KEY")
BASE_URL = os.getenv("SILICONFLOW_BASE_URL", "https://api.siliconflow.cn/v1")
MODEL = os.getenv("SILICONFLOW_MODEL", "Qwen/Qwen2-7B-Instruct")

async def test():
    print(f"[TEST] Using model: {MODEL}")
    print(f"[TEST] Base URL: {BASE_URL}")
    print(f"[TEST] API Key: {API_KEY[:10]}...")

    client = AsyncOpenAI(
        api_key=API_KEY,
        base_url=BASE_URL
    )

    try:
        response = await client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "你是一个健康助手"},
                {"role": "user", "content": "我血糖高怎么办？"}
            ],
            temperature=0.7,
            max_tokens=500
        )
        print(f"[SUCCESS] Response: {response.choices[0].message.content}")
    except Exception as e:
        print(f"[ERROR] {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(test())
