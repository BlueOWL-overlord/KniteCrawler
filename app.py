import subprocess
import os
import shutil
from flask import Flask, request, render_template, redirect, url_for, send_file, jsonify
from flask_socketio import SocketIO, emit
import io
import csv
from .db import init_db, load_settings, get_terms, get_results, get_crawl_history, add_term, update_settings
from .trackers import TrackerManager, DarkWebTracker, FourChanTracker, RedditTracker, TelegramTracker, DiscordTracker, XTracker, PastebinTracker, GitHubTracker, XSSTracker, ExploitTracker, NulledTracker
from datetime import datetime, timedelta
import time
import logging

# Configure logging
logging.basicConfig(
    filename=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'knitecrawler.log'),
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# Get the directory of this file (KniteCrawler/)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')

# Ensure templates directory exists
if not os.path.exists(TEMPLATES_DIR):
    os.makedirs(TEMPLATES_DIR)

app = Flask(__name__, template_folder=TEMPLATES_DIR)
socketio = SocketIO(app)

def start_tor():
    tor_path = os.path.join(BASE_DIR, "tor", "tor.exe" if os.name == 'nt' else "tor")
    if not os.path.exists(tor_path):
        system_tor = shutil.which("tor")
        if system_tor:
            tor_path = system_tor
            logger.info(f"Using system Tor at {tor_path}")
        else:
            logger.error("Tor binary not found in 'tor/' folder or system PATH.")
            raise Exception("Tor binary not found in 'tor/' folder or system PATH.")
    logger.info(f"Starting Tor process from {tor_path}")
    tor_process = subprocess.Popen([tor_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(5)
    return tor_process

# Initialize the database
init_db()
settings = load_settings()
tracker_manager = TrackerManager(settings, emit)

tracker_manager.register_tracker('dark_web', DarkWebTracker)
tracker_manager.register_tracker('4chan', FourChanTracker)
tracker_manager.register_tracker('reddit', RedditTracker)
tracker_manager.register_tracker('telegram', TelegramTracker)
tracker_manager.register_tracker('discord', DiscordTracker)
tracker_manager.register_tracker('x', XTracker)
tracker_manager.register_tracker('pastebin', PastebinTracker)
tracker_manager.register_tracker('github', GitHubTracker)
tracker_manager.register_tracker('xss', XSSTracker)
tracker_manager.register_tracker('exploit', ExploitTracker)
tracker_manager.register_tracker('nulled', NulledTracker)

@app.route('/', methods=['GET'])
def dashboard():
    terms = get_terms()
    results = get_results()
    total_findings = len(results)
    platforms = len(set(row[1] for row in results))
    recent_alerts = [r for r in results if datetime.strptime(r[6], '%a %b %d %H:%M:%S %Y') > datetime.now() - timedelta(hours=24)]
    platforms_count = {}
    time_series = {}
    platforms_list = list(set(row[1] for row in results))
    sentiments_list = list(set(row[4] for row in results))
    for r in results:
        platforms_count[r[1]] = platforms_count.get(r[1], 0) + 1
        date = datetime.strptime(r[6], '%a %b %d %H:%M:%S %Y').strftime('%Y-%m-%d')
        time_series[date] = time_series.get(date, 0) + 1
    
    logger.info("Dashboard accessed")
    return render_template('index.html', terms=terms, results=results, total_findings=total_findings, platforms=platforms, recent_alerts=len(recent_alerts), platforms_count=platforms_count, time_series=time_series, platforms_list=platforms_list, sentiments_list=sentiments_list)

@app.route('/settings', methods=['GET', 'POST'])
def settings_page():
    global settings
    if request.method == 'POST':
        update_settings(request.form)
        settings = load_settings()
        logger.info("Settings updated")
        return redirect(url_for('settings_page'))
    logger.info("Settings page accessed")
    return render_template('settings.html', settings=settings)

@app.route('/crawl_history', methods=['GET'])
def crawl_history():
    history = get_crawl_history()
    logger.info("Crawl history accessed")
    return render_template('crawl_history.html', history=history)

@app.route('/readme', methods=['GET'])
def readme():
    logger.info("README accessed")
    return render_template('readme.html')

@app.route('/add_term', methods=['POST'])
def add_term_route():
    term = request.form.get('term')
    if term:
        add_term(term)
        logger.info(f"Term added: {term}")
    return redirect(url_for('dashboard'))

@app.route('/export', methods=['GET'])
def export_results():
    results = get_results()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Term', 'Platform', 'URL', 'Content', 'Sentiment', 'Summary', 'Timestamp'])
    writer.writerows(results)
    output.seek(0)
    logger.info("Results exported to CSV")
    return send_file(io.BytesIO(output.getvalue().encode('utf-8')), mimetype='text/csv', as_attachment=True, download_name='knitecrawler_results.csv')

@app.route('/active_trackers', methods=['GET'])
def get_active_trackers():
    active = tracker_manager.get_active_trackers()
    logger.info("Active trackers requested")
    return jsonify(active)

@app.route('/active_logs', methods=['GET'])
def get_active_logs():
    logs = tracker_manager.get_active_logs()
    logger.info("Active logs requested")
    return jsonify(logs)

@socketio.on('connect')
def handle_connect():
    logger.info("Client connected via WebSocket")

dashboard_template = """
<!DOCTYPE html>
<html>
<head>
    <title>KniteCrawler Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.socket.io/4.0.0/socket.io.min.js"></script>
    <style>
        body { background: #1a1a1a; color: #00ff00; font-family: 'Courier New', monospace; }
        .navbar { background: #0d0d0d; }
        .navbar-brand, .nav-link { color: #00ff00 !important; }
        .card { background: #2a2a2a; border: 1px solid #00ff00; }
        .card-body { color: #00ff00; }
        .btn-primary { background: #00ff00; border: none; color: #000; }
        .btn-primary:hover { background: #00cc00; }
        .search-container { margin: 20px 0; }
        .search-bar { width: 70%; padding: 10px; background: #2a2a2a; color: #00ff00; border: 1px solid #00ff00; }
        .filter-container { margin-bottom: 20px; }
        .filter-select { background: #2a2a2a; color: #00ff00; border: 1px solid #00ff00; padding: 5px; }
        .result-item { border-bottom: 1px solid #00ff00; padding: 15px 0; }
        .result-title { color: #00ff00; font-size: 18px; }
        .result-url { color: #00cc00; font-size: 14px; }
        .result-snippet { color: #00ff00; font-size: 14px; }
        .highlight { background: #ff00ff; color: #000; padding: 2px; }
        .score { color: #ff00ff; font-weight: bold; }
        .activity-container { margin-top: 20px; }
        .activity-list { list-style-type: none; padding: 0; }
        .activity-item { padding: 5px; background: #2a2a2a; margin-bottom: 5px; border: 1px solid #00ff00; }
        .logs-container { margin-top: 20px; max-height: 200px; overflow-y: auto; background: #2a2a2a; border: 1px solid #00ff00; padding: 10px; }
        .log-item { margin-bottom: 5px; }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg">
        <div class="container">
            <a class="navbar-brand" href="/">KniteCrawler</a>
            <div class="navbar-nav">
                <a class="nav-link" href="/settings">Settings</a>
                <a class="nav-link" href="/crawl_history">Crawl History</a>
                <a class="nav-link" href="/readme">README</a>
                <a class="nav-link" href="/export">Export CSV</a>
            </div>
        </div>
    </nav>
    <div class="container mt-4">
        <h1>Dashboard</h1>
        <div class="row">
            <div class="col-md-4"><div class="card"><div class="card-body"><h5>Total Findings</h5><p>{{ total_findings }}</p></div></div></div>
            <div class="col-md-4"><div class="card"><div class="card-body"><h5>Platforms Monitored</h5><p>{{ platforms }}</p></div></div></div>
            <div class="col-md-4"><div class="card"><div class="card-body"><h5>Recent Alerts (24h)</h5><p>{{ recent_alerts }}</p></div></div></div>
        </div>
        <div class="row mt-4">
            <div class="col-md-6"><canvas id="platformChart"></canvas></div>
            <div class="col-md-6"><canvas id="timeChart"></canvas></div>
        </div>
        <div class="mt-4">
            <h2>Add Target</h2>
            <form method="POST" action="/add_term" class="mb-3">
                <div class="input-group">
                    <input type="text" name="term" class="form-control" placeholder="> Enter target" style="background: #2a2a2a; color: #00ff00; border: 1px solid #00ff00;" required>
                    <button type="submit" class="btn btn-primary">> Deploy</button>
                </div>
            </form>
            <h2>Active Targets</h2>
            <ul class="list-group mb-3">
                {% for term in terms %}
                    <li class="list-group-item" style="background: #2a2a2a; border: 1px solid #00ff00;">{{ term }}</li>
                {% endfor %}
            </ul>
            <h2>Running Activity</h2>
            <div class="activity-container">
                <ul id="activityList" class="activity-list"></ul>
            </div>
            <h2>Current Activity Status</h2>
            <div class="logs-container" id="logsList"></div>
            <h2>Intel Feed</h2>
            <div class="search-container">
                <input type="text" id="searchInput" class="search-bar" placeholder="> Search intel...">
            </div>
            <div class="filter-container">
                <select id="platformFilter" class="filter-select">
                    <option value="">All Origins</option>
                    {% for platform in platforms_list %}
                        <option value="{{ platform }}">{{ platform }}</option>
                    {% endfor %}
                </select>
                <select id="sentimentFilter" class="filter-select">
                    <option value="">All Sentiments</option>
                    {% for sentiment in sentiments_list %}
                        <option value="{{ sentiment }}">{{ sentiment }}</option>
                    {% endfor %}
                </select>
            </div>
            <div id="results">
                {% for result in results %}
                    <div class="result-item" data-term="{{ result[0] }}" data-platform="{{ result[1] }}" data-sentiment="{{ result[4] }}">
                        <div class="result-title">{{ result[0] }} - {{ result[1] }} ({{ result[6] }}) <span class="score">[Score: N/A]</span></div>
                        <div class="result-url"><a href="{{ result[2] }}">{{ result[2] }}</a></div>
                        <div class="result-snippet">{{ result[3]|replace(result[0], '<span class="highlight">' + result[0] + '</span>')|safe }} | Sentiment: {{ result[4] }} | Summary: {{ result[5] }}</div>
                    </div>
                {% endfor %}
            </div>
        </div>
    </div>
    <script>
        const socket = io();
        socket.on('new_result', function(data) {
            const resultsDiv = document.getElementById('results');
            const item = document.createElement('div');
            item.className = 'result-item';
            item.dataset.term = data.term;
            item.dataset.platform = data.platform;
            item.dataset.sentiment = data.sentiment;
            item.innerHTML = `
                <div class="result-title">${data.term} - ${data.platform} (${data.timestamp}) <span class="score">[Score: ${data.score || 'N/A'}]</span></div>
                <div class="result-url"><a href="${data.url}">${data.url}</a></div>
                <div class="result-snippet">${data.content.replace(data.term, '<span class="highlight">' + data.term + '</span>')} | Sentiment: ${data.sentiment} | Summary: ${data.summary}</div>
            `;
            resultsDiv.insertBefore(item, resultsDiv.firstChild);
            filterResults();

            if (Notification.permission === "granted") {
                new Notification(`New Intel: ${data.term}`, { body: `${data.platform}: ${data.summary} (Score: ${data.score || 'N/A'})`, icon: 'https://via.placeholder.com/32x32.png?text=KC' });
            } else if (Notification.permission !== "denied") {
                Notification.requestPermission().then(permission => {
                    if (permission === "granted") {
                        new Notification(`New Intel: ${data.term}`, { body: `${data.platform}: ${data.summary} (Score: ${data.score || 'N/A'})`, icon: 'https://via.placeholder.com/32x32.png?text=KC' });
                    }
                });
            }
        });

        new Chart(document.getElementById('platformChart').getContext('2d'), {
            type: 'bar',
            data: { labels: {{ platforms_count.keys()|list|tojson }}, datasets: [{ label: 'Findings per Origin', data: {{ platforms_count.values()|list|tojson }}, backgroundColor: '#00ff00', borderColor: '#00cc00', borderWidth: 1 }] },
            options: { scales: { y: { beginAtZero: true, ticks: { color: '#00ff00' } }, x: { ticks: { color: '#00ff00' } } }, plugins: { legend: { labels: { color: '#00ff00' } } } }
        });
        new Chart(document.getElementById('timeChart').getContext('2d'), {
            type: 'line',
            data: { labels: {{ time_series.keys()|list|tojson }}, datasets: [{ label: 'Intel Over Time', data: {{ time_series.values()|list|tojson }}, fill: false, borderColor: '#00ff00', tension: 0.1 }] },
            options: { scales: { y: { ticks: { color: '#00ff00' } }, x: { ticks: { color: '#00ff00' } } }, plugins: { legend: { labels: { color: '#00ff00' } } } }
        });

        function filterResults() {
            const searchValue = document.getElementById('searchInput').value.toLowerCase();
            const platformFilter = document.getElementById('platformFilter').value;
            const sentimentFilter = document.getElementById('sentimentFilter').value;
            const results = document.getElementsByClassName('result-item');

            for (let item of results) {
                const term = item.dataset.term.toLowerCase();
                const platform = item.dataset.platform;
                const sentiment = item.dataset.sentiment;
                const content = item.querySelector('.result-snippet').textContent.toLowerCase();
                const matchesSearch = term.includes(searchValue) || content.includes(searchValue);
                const matchesPlatform = !platformFilter || platform === platformFilter;
                const matchesSentiment = !sentimentFilter || sentiment === sentimentFilter;

                item.style.display = matchesSearch && matchesPlatform && matchesSentiment ? '' : 'none';
            }
        }

        document.getElementById('searchInput').addEventListener('input', filterResults);
        document.getElementById('platformFilter').addEventListener('change', filterResults);
        document.getElementById('sentimentFilter').addEventListener('change', filterResults);

        function updateActivity() {
            fetch('/active_trackers')
                .then(response => response.json())
                .then(data => {
                    const activityList = document.getElementById('activityList');
                    activityList.innerHTML = '';
                    if (Object.keys(data).length === 0) {
                        const li = document.createElement('li');
                        li.className = 'activity-item';
                        li.textContent = 'No active trackers running.';
                        activityList.appendChild(li);
                    } else {
                        for (const [tracker, keywords] of Object.entries(data)) {
                            const li = document.createElement('li');
                            li.className = 'activity-item';
                            li.textContent = `${tracker}: Searching for ${keywords.join(', ')}`;
                            activityList.appendChild(li);
                        }
                    }
                })
                .catch(error => console.error('Error fetching active trackers:', error));
        }

        function updateLogs() {
            fetch('/active_logs')
                .then(response => response.json())
                .then(data => {
                    const logsList = document.getElementById('logsList');
                    logsList.innerHTML = '';
                    data.forEach(log => {
                        const div = document.createElement('div');
                        div.className = 'log-item';
                        div.textContent = log;
                        logsList.appendChild(div);
                    });
                    logsList.scrollTop = logsList.scrollHeight; // Auto-scroll to bottom
                })
                .catch(error => console.error('Error fetching logs:', error));
        }

        setInterval(updateActivity, 5000);
        setInterval(updateLogs, 2000); // Update logs more frequently
        updateActivity();
        updateLogs();
    </script>
</body>
</html>
"""

settings_template = """
<!DOCTYPE html>
<html>
<head>
    <title>KniteCrawler Settings</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: #1a1a1a; color: #00ff00; font-family: 'Courier New', monospace; }
        .navbar { background: #0d0d0d; }
        .navbar-brand, .nav-link { color: #00ff00 !important; }
        .form-control { background: #2a2a2a; color: #00ff00; border: 1px solid #00ff00; }
        .btn-primary { background: #00ff00; border: none; color: #000; }
        .btn-primary:hover { background: #00cc00; }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg">
        <div class="container">
            <a class="navbar-brand" href="/">KniteCrawler</a>
            <div class="navbar-nav">
                <a class="nav-link" href="/">Dashboard</a>
                <a class="nav-link" href="/crawl_history">Crawl History</a>
                <a class="nav-link" href="/readme">README</a>
            </div>
        </div>
    </nav>
    <div class="container mt-4">
        <h1>Settings</h1>
        <form method="POST">
            <h3>Reddit</h3>
            <div class="mb-3"><label class="form-label">Client ID</label><input type="text" name="reddit_client_id" class="form-control" value="{{ settings.reddit_client_id }}"></div>
            <div class="mb-3"><label class="form-label">Client Secret</label><input type="text" name="reddit_client_secret" class="form-control" value="{{ settings.reddit_client_secret }}"></div>
            <div class="mb-3"><label class="form-label">User Agent</label><input type="text" name="reddit_user_agent" class="form-control" value="{{ settings.reddit_user_agent }}"></div>
            <h3>Telegram</h3>
            <div class="mb-3"><label class="form-label">API ID</label><input type="text" name="telegram_api_id" class="form-control" value="{{ settings.telegram_api_id }}"></div>
            <div class="mb-3"><label class="form-label">API Hash</label><input type="text" name="telegram_api_hash" class="form-control" value="{{ settings.telegram_api_hash }}"></div>
            <div class="mb-3"><label class="form-label">Phone Number</label><input type="text" name="telegram_phone" class="form-control" value="{{ settings.telegram_phone }}"></div>
            <div class="mb-3"><label class="form-label">Channel</label><input type="text" name="telegram_channel" class="form-control" value="{{ settings.telegram_channel }}"></div>
            <h3>Discord</h3>
            <div class="mb-3"><label class="form-label">Bot Token</label><input type="text" name="discord_token" class="form-control" value="{{ settings.discord_token }}"></div>
            <h3>General</h3>
            <div class="mb-3"><label class="form-label">Dark Web URLs</label><input type="text" name="dark_web_urls" class="form-control" value="{{ settings.dark_web_urls }}"></div>
            <div class="mb-3"><label class="form-label">4chan URL</label><input type="text" name="4chan_url" class="form-control" value="{{ settings['4chan_url'] }}"></div>
            <div class="mb-3"><label class="form-label">X URL</label><input type="text" name="x_url" class="form-control" value="{{ settings.x_url }}"></div>
            <div class="mb-3"><label class="form-label">Pastebin URL</label><input type="text" name="pastebin_url" class="form-control" value="{{ settings.pastebin_url }}"></div>
            <div class="mb-3"><label class="form-label">GitHub URL</label><input type="text" name="github_url" class="form-control" value="{{ settings.github_url }}"></div>
            <div class="mb-3"><label class="form-label">XSS.is URL</label><input type="text" name="xss_url" class="form-control" value="{{ settings.xss_url }}"></div>
            <div class="mb-3"><label class="form-label">Exploit.in URL</label><input type="text" name="exploit_url" class="form-control" value="{{ settings.exploit_url }}"></div>
            <div class="mb-3"><label class="form-label">Nulled.to URL</label><input type="text" name="nulled_url" class="form-control" value="{{ settings.nulled_url }}"></div>
            <div class="mb-3"><label class="form-label">Max Depth</label><input type="number" name="max_depth" class="form-control" value="{{ settings.max_depth }}"></div>
            <div class="mb-3"><label class="form-label">Max URLs</label><input type="number" name="max_urls" class="form-control" value="{{ settings.max_urls }}"></div>
            <div class="mb-3"><label class="form-label">Threads</label><input type="number" name="threads" class="form-control" value="{{ settings.threads }}"></div>
            <div class="mb-3"><label class="form-label">Proxy List</label><input type="text" name="proxy_list" class="form-control" value="{{ settings.proxy_list }}"></div>
            <div class="mb-3"><label class="form-label">2Captcha API Key</label><input type="text" name="captcha_key" class="form-control" value="{{ settings.captcha_key }}"></div>
            <button type="submit" class="btn btn-primary">> Save Config</button>
        </form>
    </div>
</body>
</html>
"""

crawl_history_template = """
<!DOCTYPE html>
<html>
<head>
    <title>KniteCrawler Crawl History</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: #1a1a1a; color: #00ff00; font-family: 'Courier New', monospace; }
        .navbar { background: #0d0d0d; }
        .navbar-brand, .nav-link { color: #00ff00 !important; }
        .table { color: #00ff00; background: #2a2a2a; }
        .table-striped tbody tr:nth-of-type(odd) { background: #333333; }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg">
        <div class="container">
            <a class="navbar-brand" href="/">KniteCrawler</a>
            <div class="navbar-nav">
                <a class="nav-link" href="/">Dashboard</a>
                <a class="nav-link" href="/settings">Settings</a>
                <a class="nav-link" href="/readme">README</a>
            </div>
        </div>
    </nav>
    <div class="container mt-4">
        <h1>Crawl History</h1>
        <table class="table table-striped">
            <thead><tr><th>URL</th><th>Discovered</th><th>Last Crawled</th><th>Status</th></tr></thead>
            <tbody>
                {% for entry in history %}
                    <tr><td>{{ entry[0] }}</td><td>{{ entry[1] }}</td><td>{{ entry[2] }}</td><td>{{ entry[3] }}</td></tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</body>
</html>
"""

readme_template = """
<!DOCTYPE html>
<html>
<head>
    <title>KniteCrawler README</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: #1a1a1a; color: #00ff00; font-family: 'Courier New', monospace; }
        .navbar { background: #0d0d0d; }
        .navbar-brand, .nav-link { color: #00ff00 !important; }
        h1, h2, h3 { color: #00ff00; }
        .container { max-width: 800px; }
        .section { margin-bottom: 20px; }
        code { background: #2a2a2a; padding: 2px 5px; border: 1px solid #00ff00; }
        pre { background: #2a2a2a; padding: 10px; border: 1px solid #00ff00; overflow-x: auto; }
        a { color: #00cc00; }
        a:hover { color: #00ff00; }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg">
        <div class="container">
            <a class="navbar-brand" href="/">KniteCrawler</a>
            <div class="navbar-nav">
                <a class="nav-link" href="/">Dashboard</a>
                <a class="nav-link" href="/settings">Settings</a>
                <a class="nav-link" href="/crawl_history">Crawl History</a>
            </div>
        </div>
    </nav>
    <div class="container mt-4">
        <h1>KniteCrawler README</h1>
        <div class="section">
            <h2>> Overview</h2>
            <p>KniteCrawler is a dark web and surface web intelligence tool designed to track leaks across multiple platforms, including Dread-like forums, Reddit, Telegram, Discord, and more. It uses AI for sentiment analysis and summarization, with real-time alerts via WebSockets and browser notifications.</p>
        </div>
        <div class="section">
            <h2>> Features</h2>
            <ul>
                <li>Multi-platform tracking: Dark Web (Dread-like), 4chan, Reddit, Telegram, Discord, X, Pastebin, GitHub, XSS.is, Exploit.in, Nulled.to</li>
                <li>Leak detection: Emails, hashes, passwords, credit cards, IPs, SSNs with weighted scoring</li>
                <li>Google-like search UI with filters (platform, sentiment)</li>
                <li>Real-time updates and browser notifications</li>
                <li>Modular tracker system for easy extension</li>
                <li>Tor integration for dark web access</li>
                <li>Export findings as CSV</li>
            </ul>
        </div>
        <div class="section">
            <h2>> Setup</h2>
            <p>1. Install dependencies:</p>
            <pre>pip install flask flask-socketio requests beautifulsoup4 stem sqlite3 praw telethon discord.py transformers torch 2captcha-python</pre>
            <p>2. Place Tor binary in <code>tor/</code> folder.</p>
            <p>3. Run the app:</p>
            <pre>cd /path/to/parent/of/KniteCrawler; python3 -m KniteCrawler.app</pre>
            <p>4. Access at <a href="http://127.0.0.1:5000">http://127.0.0.1:5000</a>.</p>
            <p>5. Configure settings at <a href="/settings">/settings</a> (e.g., API keys, dark web URLs).</p>
        </div>
        <div class="section">
            <h2>> Usage</h2>
            <p>- <strong>Dashboard</strong>: Add targets (keywords) and monitor the Intel Feed.</p>
            <p>- <strong>Search & Filter</strong>: Use the search bar and dropdowns to refine results.</p>
            <p>- <strong>Settings</strong>: Configure platform credentials and crawler options.</p>
            <p>- <strong>Crawl History</strong>: View dark web crawl logs.</p>
            <p>- <strong>Export</strong>: Download findings as CSV.</p>
        </div>
        <div class="section">
            <h2>> Dark Web Tracking</h2>
            <p>Targets Dread-like forums specified in <code>dark_web_urls</code> (comma-separated). Example:</p>
            <pre>http://dread.onion,http://darkforum.onion</pre>
            <p>Detects leaks with scores:</p>
            <ul>
                <li>Keyword: 1pt</li>
                <li>Email: 5pt</li>
                <li>Hash: 3pt</li>
                <li>Password: 10pt</li>
                <li>Credit Card: 15pt</li>
                <li>IP: 2pt</li>
                <li>SSN: 20pt</li>
            </ul>
        </div>
        <div class="section">
            <h2>> Extending Trackers</h2>
            <p>Create a new tracker in <code>trackers.py</code>:</p>
            <pre>
class CustomTracker(BaseTracker):
    def track(self, keyword):
        spider = Spider(self.settings, self.settings.get('captcha_key'))
        spider.run(keyword, "https://customsite.com", "Custom", self.emit_callback)
            </pre>
            <p>Register in <code>app.py</code>:</p>
            <pre>tracker_manager.register_tracker('custom', CustomTracker)</pre>
        </div>
        <div class="section">
            <h2>> Notes</h2>
            <p>- Requires Tor for dark web access.</p>
            <p>- Adjust <code>max_depth</code>, <code>max_urls</code>, and <code>threads</code> for performance.</p>
            <p>- Use real .onion URLs for effective dark web tracking.</p>
        </div>
    </div>
</body>
</html>
"""

if __name__ == "__main__":
    logger.info("Starting KniteCrawler application")
    tor_process = start_tor()
    
    terms = get_terms()
    if terms:
        tracker_manager.start()
    
    with open(os.path.join(TEMPLATES_DIR, 'index.html'), 'w') as f:
        f.write(dashboard_template)
    with open(os.path.join(TEMPLATES_DIR, 'settings.html'), 'w') as f:
        f.write(settings_template)
    with open(os.path.join(TEMPLATES_DIR, 'crawl_history.html'), 'w') as f:
        f.write(crawl_history_template)
    with open(os.path.join(TEMPLATES_DIR, 'readme.html'), 'w') as f:
        f.write(readme_template)
    
    try:
        logger.info("Starting Flask server")
        socketio.run(app, debug=True, use_reloader=False)
    finally:
        logger.info("Terminating Tor process")
        tor_process.terminate()
