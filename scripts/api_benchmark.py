import asyncio
import time
import httpx
import json
import os
from datetime import datetime

# 配置 - 优先从环境变量读取，否则使用默认值
UPSTREAM_URL = os.getenv("UPSTREAM_URL", "https://model.zhengshuyun.net/v1/responses")
PROXY_URL = os.getenv("PROXY_URL", "http://141.148.136.194:8059/v1/responses")
PROMPT = "请写一篇200字左右的关于人工智能（AI）的简要介绍，涵盖其定义、应用领域及未来潜力。"
MODEL = os.getenv("MODEL_NAME", "gpt-5.4")

async def test_api(client, name, url, key):
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    
    # 确保 URL 正确指向 responses 接口
    if "/v1/chat/completions" in url:
        url = url.replace("/v1/chat/completions", "/v1/responses")
    elif not url.endswith("/v1/responses") and not url.endswith("/responses"):
        url = url.rstrip("/") + "/v1/responses"
    
    payload = {"model": MODEL, "messages": [{"role": "user", "content": PROMPT}], "stream": True}
    
    start = time.perf_counter()
    ttfb = None
    full_text = ""
    
    try:
        async with client.stream("POST", url, headers=headers, json=payload, timeout=30.0) as resp:
            if resp.status_code != 200: 
                error_body = await resp.aread()
                return {"name": name, "error": f"Error {resp.status_code}: {error_body.decode()}", "status": "Failed"}
            
            async for line in resp.aiter_lines():
                if not ttfb: ttfb = time.perf_counter() - start
                if line.startswith("data: ") and " [DONE]" not in line:
                    try:
                        data = json.loads(line[6:])
                        if 'choices' in data and len(data['choices']) > 0:
                            choice = data['choices'][0]
                            content = ""
                            if 'delta' in choice:
                                content = choice['delta'].get('content', '')
                            elif 'message' in choice:
                                content = choice['message'].get('content', '')
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
    # 从 Secrets 中获取 Key
    upstream_key = os.getenv("UPSTREAM_KEY")
    proxy_key = os.getenv("PROXY_KEY")
    
    if not upstream_key or not proxy_key:
        print("错误: 请先在 GitHub Secrets 中设置 UPSTREAM_KEY 和 PROXY_KEY")
        return

    async with httpx.AsyncClient(verify=False) as client:
        print(f"开始测试...\n上游地址: {UPSTREAM_URL}\n中转地址: {PROXY_URL}\n")
        results = await asyncio.gather(
            test_api(client, "上游渠道商 (Upstream)", UPSTREAM_URL, upstream_key),
            test_api(client, "我们的平台 (Our Proxy)", PROXY_URL, proxy_key)
        )
    
    output = {
        "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "test_results": results
    }
    
    # 保存结果
    with open("api_stats.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print("测试数据已更新。")

if __name__ == "__main__":
    asyncio.run(main())
