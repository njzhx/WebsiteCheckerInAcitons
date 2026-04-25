import requests
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib3.exceptions import InsecureRequestWarning

# 禁用 SSL 警告
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# 模拟真实 Chrome 浏览器的完整请求头
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Cache-Control": "max-age=0",
}

TIMEOUT = 15          # 连接超时（秒）
MAX_WORKERS = 10      # 并发线程数

def load_urls(filepath):
    """从 txt 文件加载 URL 列表，跳过空行和注释行"""
    urls = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                urls.append(line)
    return urls

def check_url(url):
    """对单个 URL 发起 GET 请求，模拟真实浏览器访问，返回 (url, status_code, error_msg)"""
    try:
        resp = requests.get(
            url,
            headers=HEADERS,
            timeout=TIMEOUT,
            allow_redirects=True,
            verify=False,       # 忽略 SSL 证书错误
            stream=True         # 流式读取，只取前 1KB 避免下载整个页面
        )
        # 读取一小部分内容后立即关闭连接，模拟真实访问但节省带宽
        resp.close()
        return (url, resp.status_code, None)
    except requests.exceptions.Timeout:
        return (url, None, "超时")
    except requests.exceptions.ConnectionError:
        return (url, None, "连接失败")
    except Exception as e:
        return (url, None, f"未知错误: {str(e)}")

def main():
    urls = load_urls("urls.txt")
    if not urls:
        print("❌ urls.txt 中没有有效的 URL，请检查文件内容。")
        sys.exit(1)

    print(f"开始检测 {len(urls)} 个 URL，并发数: {MAX_WORKERS}，超时: {TIMEOUT}s")
    print(f"请求方式: GET（模拟 Chrome 浏览器）\\n")
    print("=" * 80)

    results = {"成功": [], "其他": [], "失败": []}

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_url = {executor.submit(check_url, url): url for url in urls}
        for future in as_completed(future_to_url):
            url, status_code, error = future.result()
            if error:
                results["失败"].append((url, error))
                print(f"❌ 失败 | {url} | {error}")
            elif 200 <= status_code < 300:
                results["成功"].append((url, status_code))
                print(f"✅ 成功 | {url} | HTTP {status_code}")
            else:
                results["其他"].append((url, status_code))
                print(f"🔵 其他 | {url} | HTTP {status_code}")

    print("\\n" + "=" * 80)
    print("📊 检测结果汇总:")
    print(f"   ✅ 可正常访问: {len(results['成功'])} 个")
    print(f"   🔵 其他状态码 (非2xx): {len(results['其他'])} 个")
    print(f"   ❌ 连接失败/超时: {len(results['失败'])} 个")

    if results["失败"]:
        sys.exit(1)

if __name__ == "__main__":
    main()
