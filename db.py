import sqlite3
from datetime import datetime

DB_NAME = "leak_finder.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS terms (
        term TEXT PRIMARY KEY
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS results (
        term TEXT,
        platform TEXT,
        url TEXT,
        content TEXT,
        sentiment TEXT,
        summary TEXT,
        timestamp TEXT
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS onion_urls (
        url TEXT PRIMARY KEY,
        discovered TEXT,
        last_crawled TEXT,
        status TEXT
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )''')
    
    # Insert default settings if they don’t exist
    default_settings = [
        ('reddit_client_id', ''),
        ('reddit_client_secret', ''),
        ('reddit_user_agent', 'KniteCrawler/1.0'),
        ('telegram_api_id', '0'),  # Default to '0' as a placeholder
        ('telegram_api_hash', ''),
        ('telegram_phone', ''),
        ('telegram_channel', ''),
        ('discord_token', ''),
        ('dark_web_urls', 'http://dread.onion'),
        ('4chan_url', 'https://4chan.org'),
        ('x_url', 'https://x.com'),
        ('pastebin_url', 'https://pastebin.com'),
        ('github_url', 'https://github.com'),
        ('xss_url', 'https://xss.is'),
        ('exploit_url', 'https://exploit.in'),
        ('nulled_url', 'https://nulled.to'),
        ('max_depth', '2'),
        ('max_urls', '100'),
        ('threads', '4'),
        ('proxy_list', ''),
        ('captcha_key', '')
    ]
    
    c.executemany('INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)', default_settings)
    
    conn.commit()
    conn.close()

def load_settings():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT key, value FROM settings")
    settings = {row[0]: row[1] for row in c.fetchall()}
    conn.close()
    return settings

def get_terms():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT term FROM terms")
    terms = [row[0] for row in c.fetchall()]
    conn.close()
    return terms

def get_results():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT term, platform, url, content, sentiment, summary, timestamp FROM results")
    results = c.fetchall()
    conn.close()
    return results

def get_crawl_history():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT url, discovered, last_crawled, status FROM onion_urls")
    history = c.fetchall()
    conn.close()
    return history

def add_term(term):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO terms (term) VALUES (?)", (term,))
    conn.commit()
    conn.close()

def update_settings(form_data):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    for key, value in form_data.items():
        c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

def update_onion_url(url, status):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute('''INSERT OR REPLACE INTO onion_urls (url, discovered, last_crawled, status)
                 VALUES (?, ?, ?, ?)''', 
                 (url, now, now, status))
    conn.commit()
    conn.close()

def insert_result(term, platform, url, content, sentiment, summary):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    timestamp = datetime.now().strftime('%a %b %d %H:%M:%S %Y')
    c.execute('''INSERT INTO results (term, platform, url, content, sentiment, summary, timestamp)
                 VALUES (?, ?, ?, ?, ?, ?, ?)''', 
                 (term, platform, url, content, sentiment, summary, timestamp))
    conn.commit()
    conn.close()
