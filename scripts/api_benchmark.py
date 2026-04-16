import asyncio
import time
import httpx
import json
import os
from datetime import datetime

# 配置
OFFICIAL_URL = "https://api.openai.com/v1/chat/completions"
# 请在环境变量中设置 PROXY_API_URL，或者手动修改此处
PROXY_URL = os.getenv("PROXY_API_URL", "https://api.openai.com/v1/chat/completions") 
PROMPT = "请写一篇200字左右的关于人工智能（AI）的简要介绍，涵盖其定义、应用领域及未来潜力。"
MODEL = "gpt-3.5-turbo"

async def test_api(client, name, url, key):
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    payload = {"model": MODEL, "messages": [{"role": "user", "content": PROMPT}], "stream": True}
    
    start = time.perf_counter()
    ttfb = None
    full_text = ""
    
    try:
        async with client.stream("POST", url, headers=headers, json=payload, timeout=30.0) as resp:
            if resp.status_code != 200: return {"name": name, "error": f"Error {resp.status_code}", "status": "Failed"}
            async for line in resp.aiter_lines():
                if not ttfb: ttfb = time.perf_counter() - start
                if line.startswith("data: ") and " [DONE]" not in line:
                    try:
                        data = json.loads(line[6:])
                        content = data['choices'][0]['delta'].get('content', '')
                        full_text += content
                    except: pass
        
        total_time = time.perf_counter() - start
        return {
            "name": name,
            "ttfb": int(ttfb * 1000),
            "total_time": int(total_time * 1000),
            "text_sample": full_text.strip()[:200] + "...",
            "status": "Success"
        }
    except Exception as e:
        return {"name": name, "error": str(e), "status": "Failed"}

async def main():
    off_key = os.getenv("OFFICIAL_KEY")
    proxy_key = os.getenv("PROXY_KEY")
    
    if not off_key or not proxy_key:
        print("错误: 请先在仓库 Secrets 中设置 OFFICIAL_KEY 和 PROXY_KEY")
        return

    async with httpx.AsyncClient() as client:
        # 并行测试，确保网络波动影响一致
        results = await asyncio.gather(
            test_api(client, "Official OpenAI", OFFICIAL_URL, off_key),
            test_api(client, "Our Proxy API", PROXY_URL, proxy_key)
        )
    
    output = {
        "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "test_results": results
    }
    
    # 保存 JSON
    with open("api_stats.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
        
    # 更新 README 中的表格（简单演示，正式版可用模板替换）
    print("测试完成。数据已汇总。")

if __name__ == "__main__":
    asyncio.run(main())
