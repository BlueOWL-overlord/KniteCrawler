import requests
from bs4 import BeautifulSoup
from stem import Signal
from stem.control import Controller
import time
import random
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor
import heapq
from twocaptcha import TwoCaptcha
from .db import update_onion_url
import threading

class Spider:
    def __init__(self, settings, captcha_key=None, use_tor=False):
        self.settings = settings
        self.session = self.get_tor_session() if use_tor else self.get_proxy_session()
        self.captcha_solver = TwoCaptcha(captcha_key) if captcha_key else None
        self.lock = threading.Lock()

    def get_tor_session(self):
        session = requests.Session()
        session.proxies = {'http': 'socks5h://127.0.0.1:9050', 'https': 'socks5h://127.0.0.1:9050'}
        return session

    def get_proxy_session(self):
        proxy_list = self.settings.get('proxy_list', '')
        proxy = random.choice(proxy_list.split(',')) if proxy_list else None
        session = requests.Session()
        if proxy:
            session.proxies = {'http': proxy, 'https': proxy}
        return session

    def renew_tor_ip(self):
        with Controller.from_port(port=9051) as controller:
            controller.authenticate()
            controller.signal(Signal.NEWNYM)
            time.sleep(5)

    def solve_captcha(self, url):
        if not self.captcha_solver:
            return None
        try:
            result = self.captcha_solver.normal(url)
            return result['code']
        except Exception as e:
            print(f"CAPTCHA solving failed: {e}")
            return None

    def crawl_url(self, url, depth, keyword, max_depth, platform_name, visited, queue, emit_callback):
        if url in visited or depth > max_depth:
            return 0, []
        
        retries = 3
        for attempt in range(retries):
            try:
                time.sleep(random.uniform(1, 3))
                response = self.session.get(url, timeout=15)
                if "captcha" in response.text.lower() and self.captcha_solver:
                    captcha_code = self.solve_captcha(url)
                    if captcha_code:
                        response = self.session.post(url, data={'captcha': captcha_code}, timeout=15)
                response.raise_for_status()
                break
            except requests.RequestException as e:
                if attempt == retries - 1:
                    with self.lock:
                        update_onion_url(url, f"Failed: {str(e)}")
                    return 0, []
                time.sleep(2 ** attempt)
        
        with self.lock:
            visited.add(url)
            update_onion_url(url, "Success")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        page_text = soup.get_text()
        from .ai import analyze_content
        finding, sentiment, summary = analyze_content([page_text], keyword)[0]
        
        if finding['score'] > 0:
            with self.lock:
                from .db import insert_result
                content = f"Score: {finding['score']}, {str(finding.get('email', []))[:200]}"
                insert_result(keyword, platform_name, url, content, sentiment, summary)
            emit_callback({'term': keyword, 'platform': platform_name, 'url': url, 'content': content, 'sentiment': sentiment, 'summary': summary, 'timestamp': time.ctime()})
        
        links = [urljoin(url, link['href']) for link in soup.find_all('a', href=True) if urljoin(url, link['href']) not in visited]
        return finding['score'], links

    def run(self, keyword, seed_urls, platform_name, emit_callback):
        visited = set()
        queue = [(0, 0, url) for url in seed_urls.split(',')]
        heapq.heapify(queue)
        max_depth = int(self.settings.get('max_depth', 3))
        max_urls = int(self.settings.get('max_urls', 100))
        threads = int(self.settings.get('threads', 5))

        def worker():
            while queue and len(visited) < max_urls:
                with self.lock:
                    if not queue:
                        break
                    priority, depth, url = heapq.heappop(queue)
                
                score, links = self.crawl_url(url, depth, keyword, max_depth, platform_name, visited, queue, emit_callback)
                
                with self.lock:
                    new_depth = depth + 1 if score > 0 else depth
                    for link in links:
                        if link not in visited and len(visited) < max_urls:
                            heapq.heappush(queue, (-score, new_depth, link))
        
        with ThreadPoolExecutor(max_workers=threads) as executor:
            futures = [executor.submit(worker) for _ in range(threads)]
            for future in futures:
                future.result()
