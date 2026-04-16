import asyncio
import time
import httpx
import json
import os
from datetime import datetime

# 配置
UPSTREAM_URL = os.getenv("UPSTREAM_URL", "https://model.zhengshuyun.net/v1/responses")
PROXY_URL = os.getenv("PROXY_URL", "http://141.148.136.194:8059/v1/responses")
PROMPT = "请写一篇200字左右的关于人工智能（AI）的简要介绍，涵盖其定义、应用领域及未来潜力。"
MODEL = os.getenv("MODEL_NAME", "gpt-5.4")

async def test_api(client, name, url, key):
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    
    # 确保 URL 正确
    if "/v1/chat/completions" in url:
        url = url.replace("/v1/chat/completions", "/v1/responses")
    elif not url.endswith("/v1/responses") and not url.endswith("/responses"):
        url = url.rstrip("/") + "/v1/responses"
    
    payload = {
        "model": MODEL,
        "input": PROMPT,
        "messages": [{"role": "user", "content": PROMPT}],
        "stream": True
    }
    
    start = time.perf_counter()
    ttfb = None
    
    try:
        async with client.stream("POST", url, headers=headers, json=payload, timeout=30.0) as resp:
            if resp.status_code != 200: 
                error_body = await resp.aread()
                return {"name": name, "error": f"Error {resp.status_code}", "status": "Failed"}
            
            async for line in resp.aiter_lines():
                if not ttfb: ttfb = time.perf_counter() - start
                if line.startswith("data: ") and " [DONE]" not in line:
                    pass # 仅测试速度，不处理文字
        
        total_time = time.perf_counter() - start
        return {
            "name": name,
            "ttfb": int(ttfb * 1000),
            "total_time": int(total_time * 1000),
            "status": "Success"
        }
    except Exception as e:
        return {"name": name, "error": "Timeout/Network Error", "status": "Failed"}

async def main():
    upstream_key = os.getenv("UPSTREAM_KEY")
    proxy_key = os.getenv("PROXY_KEY")
    
    if not upstream_key or not proxy_key:
        print("Error: Keys not set")
        return

    async with httpx.AsyncClient(verify=False) as client:
        # 并行执行：对比上游和我们（以普通用户身份）
        results = await asyncio.gather(
            test_api(client, "官方上游 (Upstream)", UPSTREAM_URL, upstream_key),
            test_api(client, "我们的接口 (普通用户)", PROXY_URL, proxy_key)
        )
    
    output = {
        "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "test_results": results
    }
    
    # 保存 JSON
    with open("api_stats.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
        
    # 自动更新 README.md
    try:
        if os.path.exists("README.md"):
            with open("README.md", "r", encoding="utf-8") as f:
                content = f.read()
            
            table_header = "| 接口身份 | 首字延迟 (ms) | 总耗时 (ms) | 实时状态 |"
            table_separator = "| :--- | :--- | :--- | :--- |"
            rows = []
            for r in results:
                if r["status"] == "Success":
                    rows.append(f"| {r['name']} | {r['ttfb']} | {r['total_time']} | ✅ 极速 |")
                else:
                    rows.append(f"| {r['name']} | - | - | ❌ 维护中 ({r.get('error','')}) |")
            
            new_table = f"## 📈 实时性能监控 (更新时间: {output['last_update']} UTC)\n\n{table_header}\n{table_separator}\n" + "\n".join(rows)
            
            if "## 📈 实时性能监控" in content:
                parts = content.split("## 📈 实时性能监控")
                updated_content = parts[0] + new_table
            else:
                updated_content = content + "\n\n" + new_table
                
            with open("README.md", "w", encoding="utf-8") as f:
                f.write(updated_content)
    except Exception as e:
        print(f"Update failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
