import requests
from bs4 import BeautifulSoup
from .spider import Spider
from .db import get_terms
import logging
from collections import deque

# Configure logging
logger = logging.getLogger(__name__)

class BaseTracker:
    def __init__(self, settings, emit_callback):
        self.settings = settings
        self.emit_callback = emit_callback

    def track(self, keyword):
        raise NotImplementedError("Subclasses must implement track()")

class TrackerManager:
    def __init__(self, settings, emit_callback):
        self.settings = settings
        self.emit_callback = emit_callback
        self.trackers = {}
        self.active_trackers = {}
        self.active_logs = deque(maxlen=100)  # Store last 100 logs
        import threading
        self.lock = threading.Lock()

    def register_tracker(self, name, tracker_class):
        self.trackers[name] = tracker_class(self.settings, self.emit_callback)

    def start(self):
        logger.info("Starting trackers...")
        self.active_logs.append("TrackerManager: Starting trackers...")
        terms = get_terms()
        if not terms:
            logger.warning("No terms to track.")
            self.active_logs.append("TrackerManager: No terms to track.")
            return
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor() as executor:
            for name, tracker in self.trackers.items():
                for keyword in terms:
                    with self.lock:
                        if name not in self.active_trackers:
                            self.active_trackers[name] = []
                        if keyword not in self.active_trackers[name]:
                            self.active_trackers[name].append(keyword)
                            logger.info(f"Starting {name} tracker for keyword: {keyword}")
                            self.active_logs.append(f"Starting {name} tracker for keyword: {keyword}")
                    executor.submit(self._track_with_cleanup, name, tracker, keyword)

    def _track_with_cleanup(self, name, tracker, keyword):
        try:
            tracker.track(keyword)
            with self.lock:
                logger.info(f"{name} completed tracking for {keyword}")
                self.active_logs.append(f"{name} completed tracking for {keyword}")
        except Exception as e:
            with self.lock:
                logger.error(f"{name} failed for {keyword}: {str(e)}")
                self.active_logs.append(f"{name} failed for {keyword}: {str(e)}")
        finally:
            with self.lock:
                if keyword in self.active_trackers.get(name, []):
                    self.active_trackers[name].remove(keyword)
                if not self.active_trackers[name]:
                    del self.active_trackers[name]

    def get_active_trackers(self):
        with self.lock:
            return self.active_trackers.copy()

    def get_active_logs(self):
        with self.lock:
            return list(self.active_logs)

class DarkWebTracker(BaseTracker):
    def track(self, keyword):
        spider = Spider(self.settings, self.settings.get('captcha_key'))
        dark_web_urls = self.settings.get('dark_web_urls', '').split(',')
        for url in dark_web_urls:
            if url.strip():
                spider.run(keyword, url.strip(), "DarkWeb", self.emit_callback)

class FourChanTracker(BaseTracker):
    def track(self, keyword):
        spider = Spider(self.settings, self.settings.get('captcha_key'))
        url = self.settings.get('4chan_url', 'https://4chan.org')
        spider.run(keyword, url, "4chan", self.emit_callback)

class RedditTracker(BaseTracker):
    def track(self, keyword):
        spider = Spider(self.settings, self.settings.get('captcha_key'))
        url = "https://reddit.com"
        spider.run(keyword, url, "Reddit", self.emit_callback)

class TelegramTracker(BaseTracker):
    def __init__(self, settings, emit_callback):
        super().__init__(settings, emit_callback)
        try:
            api_id = int(settings.get('telegram_api_id', '0'))
            api_hash = settings.get('telegram_api_hash', '')
            if api_id == 0 or not api_hash:
                logger.warning("TelegramTracker: Missing or invalid API credentials. Skipping initialization.")
                self.client = None
            else:
                from telethon import TelegramClient
                self.client = TelegramClient('session_name', api_id, api_hash)
                self.phone = settings.get('telegram_phone', '')
                self.channel = settings.get('telegram_channel', '')
        except ValueError as e:
            logger.error(f"TelegramTracker: Invalid telegram_api_id format - {e}. Skipping initialization.")
            self.client = None
        except ImportError:
            logger.error("TelegramTracker: telethon not installed. Skipping initialization.")
            self.client = None

    def track(self, keyword):
        if self.client is None:
            logger.warning("TelegramTracker: Not initialized due to missing credentials or dependencies. Skipping tracking.")
            return
        spider = Spider(self.settings, self.settings.get('captcha_key'))
        spider.run(keyword, self.channel, "Telegram", self.emit_callback)

class DiscordTracker(BaseTracker):
    def track(self, keyword):
        spider = Spider(self.settings, self.settings.get('captcha_key'))
        url = "https://discord.com"
        spider.run(keyword, url, "Discord", self.emit_callback)

class XTracker(BaseTracker):
    def track(self, keyword):
        spider = Spider(self.settings, self.settings.get('captcha_key'))
        url = self.settings.get('x_url', 'https://x.com')
        spider.run(keyword, url, "X", self.emit_callback)

class PastebinTracker(BaseTracker):
    def track(self, keyword):
        spider = Spider(self.settings, self.settings.get('captcha_key'))
        url = self.settings.get('pastebin_url', 'https://pastebin.com')
        spider.run(keyword, url, "Pastebin", self.emit_callback)

class GitHubTracker(BaseTracker):
    def track(self, keyword):
        spider = Spider(self.settings, self.settings.get('captcha_key'))
        url = self.settings.get('github_url', 'https://github.com')
        spider.run(keyword, url, "GitHub", self.emit_callback)

class XSSTracker(BaseTracker):
    def track(self, keyword):
        spider = Spider(self.settings, self.settings.get('captcha_key'))
        url = self.settings.get('xss_url', 'https://xss.is')
        spider.run(keyword, url, "XSS.is", self.emit_callback)

class ExploitTracker(BaseTracker):
    def track(self, keyword):
        spider = Spider(self.settings, self.settings.get('captcha_key'))
        url = self.settings.get('exploit_url', 'https://exploit.in')
        spider.run(keyword, url, "Exploit.in", self.emit_callback)

class NulledTracker(BaseTracker):
    def track(self, keyword):
        spider = Spider(self.settings, self.settings.get('captcha_key'))
        url = self.settings.get('nulled_url', 'https://nulled.to')
        spider.run(keyword, url, "Nulled.to", self.emit_callback)
