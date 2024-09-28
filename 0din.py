import os
import json
import time
import logging
import secrets
import requests
import threading
import sched
import search
import peer_discovery
import indexer
import psycopg2
from psycopg2 import pool, OperationalError
from datetime import datetime, timedelta
from flask import Flask, render_template, redirect, request, jsonify, flash, send_file, abort, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from colorlog import ColoredFormatter

# Logging configuration
log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
formatter = ColoredFormatter(
    "%(asctime)s - %(name)s - %(log_color)s%(levelname)s%(reset)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    log_colors={
        'DEBUG': 'cyan',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'bold_red',
    }
)
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(console_handler)

def create_db_pool():
    max_attempts = 5
    attempt = 0
    backoff_time = 1  # Initial backoff time in seconds

    while attempt < max_attempts:
        try:
            db_pool = pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=10,
                dbname=os.getenv('DB_NAME'),
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASSWORD'),
                host=os.getenv('DB_HOST', 'localhost'),
                port=os.getenv('DB_PORT', '5432')
            )
            # Test the connection
            conn = db_pool.getconn()
            db_pool.putconn(conn)  # Return the connection back to the pool
            return db_pool
        except OperationalError:
            attempt += 1
            print(f"Attempt {attempt} failed. Retrying in {backoff_time} seconds...")
            time.sleep(backoff_time)
            backoff_time *= 2  # Exponential backoff

    raise Exception("Unable to connect to the database after multiple attempts, verify your database status.")

# Usage
try:
    db_pool = create_db_pool()
    print("Database pool created successfully.")
except Exception as e:
    print(f"Error creating database pool: {e}")

# Flask application
app = Flask(__name__)
scheduler = sched.scheduler(time.time, time.sleep)
app.secret_key = secrets.token_hex(16)

# Default configuration
DEFAULT_CONFIG = {
    'NODE_ID': os.getenv('NODE_ID', '127.0.0.1:5000'),
    'LAST_EXECUTION_FILE': 'last_execution.txt',
    'INDEX_FILES_TIME': 1,
    'PEER_DISCOVER_INTERVAL': 1,
    'DIRECTORY': '/the/directory/to/be/shared',
    'URL': 'https://raw.githubusercontent.com/username/repository/branch/path/to/file.json',
    'HEARTBEAT_INTERVAL': 10,
}

# Global settings dictionary
settings = {
    'known_nodes': set(os.getenv('KNOWN_NODES', '').split(', ')),
    'announced_nodes': set(),
}

def setup_admin_credentials(username, password):
    hashed_password = generate_password_hash(password)
    with open('credentials.json', 'w') as f:
        json.dump({'username': username, 'password': hashed_password}, f)

def get_db_connection():
    try:
        conn = db_pool.getconn()
        if conn.closed != 0:
            raise psycopg2.InterfaceError("Connection is closed.")
        logger.info("Database connection retrieved from pool.")
        return conn
    except psycopg2.Error as e:
        logger.error(f"Database connection failed: {e}")
        raise

def initialize_settings():
    if not os.path.exists('settings.json'):
        with open('settings.json', 'w') as f:
            json.dump(DEFAULT_CONFIG, f, indent=4)
    with open('settings.json') as f:
        config = json.load(f)
    settings.update({key: config.get(key, value) for key, value in DEFAULT_CONFIG.items()})

def load_credentials():
    if os.path.exists('credentials.json'):
        with open('credentials.json') as f:
            return json.load(f)
    return {'username': 'admin', 'password': generate_password_hash('admin')}

@app.before_request
def check_setup():
    ssl_enabled = os.getenv("ENABLE_SSL") == "true"
    https_redirect_enabled = os.getenv("ENABLE_HTTPS_REDIRECT") == "true"

    if ssl_enabled:
        if not request.is_secure:
            url = request.url.replace("http://", "https://", 1)
            return redirect(url, code=301)
        return

    if https_redirect_enabled:
        if not request.is_secure and request.headers.get('X-Forwarded-Proto', 'http') != 'https':
            url = request.url.replace("http://", "https://", 1)
            return redirect(url, code=301)

    if request.path.startswith('/static') or request.endpoint in ['setup', 'login']:
        return

    if not os.path.exists('credentials.json'):
        return redirect(url_for('setup'))

@app.route('/setup', methods=['GET', 'POST'])
def setup():
    if os.path.exists('credentials.json'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        password_confirmation = request.form['password_confirmation']

        if (password_confirmation != password):
            flash("Passwords do not match", 'error')

            return redirect(url_for('setup'))

        setup_admin_credentials(username, password)
        return redirect(url_for('login'))
    
    return render_template('setup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        credentials = load_credentials()
        if username == credentials['username'] and check_password_hash(credentials['password'], password):
            session['logged_in'] = True
            return redirect(url_for('admin'))
        else:
            return 'Invalid credentials', 401
    return render_template('login.html')

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    config = settings.copy()

    if request.method == 'POST':
        for key in config:
            if key in request.form:
                try:
                    config[key] = json.loads(request.form[key])
                except ValueError:
                    config[key] = request.form[key]

    return render_template('admin.html', config=config)

@app.route('/shutdown', methods=['POST'])
def shutdown():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()
    return 'Server shutting down...'

@app.route('/restart', methods=['POST'])
def restart():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()
    os.execv(__file__, ['python'] + [__file__])
    return 'Server restarting...'

@app.route('/indexer', methods=['POST'])
def trigger_indexer():
    if not session.get('logged_in'):
        return "Unauthorized", 401  # Return an unauthorized response

    conn = get_db_connection()  # Call the function to get the connection

    # Assuming 'path' is passed in the POST request body
    path = request.json.get('path')  # Retrieve path from JSON payload
    if not path:
        return "Path is required", 400  # Return a bad request response if path is missing

    try:
        indexer.indexer(path, conn)  # Call the indexer function
        return "Indexer run successfully", 200  # Return success message with status code
    except Exception as e:
        return f"An error occurred: {str(e)}", 500  # Handle any exceptions

def run_indexer():
    logger.info("Running indexer...")
    conn = get_db_connection()
    indexer.indexer(settings['DIRECTORY'], conn)  # Ensure this interacts with the database correctly

    next_run = datetime.now() + timedelta(hours=24)
    delay = (next_run - datetime.now()).total_seconds()
    logger.info(f"Scheduling indexer for the next run in 24 hours")
    scheduler.enter(delay, 1, run_indexer)

def run_announcer():
    logger.info("Running announcer...")
    new_nodes_discovered = False
    for node in list(settings['known_nodes']):
        if node not in settings['announced_nodes']:
            logger.info(f"Announcing to {node}...")
            new_nodes = peer_discovery.announce(f"http://{node}/announce", settings['NODE_ID'], settings['known_nodes'])
            settings['announced_nodes'].add(node)
            if new_nodes:
                new_nodes_discovered = True
                settings['known_nodes'].update(new_nodes)
    
    logger.info(f"Known nodes: {settings['known_nodes']}")
    logger.info(f"Announced nodes: {settings['announced_nodes']}")
    
    if not new_nodes_discovered:
        logger.info("No new nodes discovered, stopping announcer.")
    
    delay = settings['PEER_DISCOVER_INTERVAL'] * 3600
    logger.info(f"Scheduling announcer for the next run in {settings['PEER_DISCOVER_INTERVAL']} hours")
    scheduler.enter(delay, 1, run_announcer)

def run_heartbeat_checker():
    logger.info("Running heartbeat checker...")
    nodes_to_remove = set()
    for node in list(settings['known_nodes']):
        result = peer_discovery.heartbeat_ping(f"http://{node}/heartbeat")
        if result == 1:
            logger.info(f"Node {node} is unreachable or invalid, removing from known_nodes.")
            nodes_to_remove.add(node)
        elif result == 2:
            logger.error("No internet connection, cannot perform heartbeat check.")
            break
    
    settings['known_nodes'].difference_update(nodes_to_remove)
    logger.info(f"Updated known nodes: {settings['known_nodes']}")
    
    delay = settings['HEARTBEAT_INTERVAL'] * 60
    logger.info(f"Scheduling heartbeat checker for the next run in {settings['HEARTBEAT_INTERVAL']} minutes")
    scheduler.enter(delay, 1, run_heartbeat_checker)

def schedule_tasks():
    now = datetime.now()
    next_index_run = datetime.combine(now.date(), datetime.min.time()) + timedelta(hours=settings['INDEX_FILES_TIME'])
    if now > next_index_run:
        next_index_run += timedelta(days=1)

    delay_index = (next_index_run - now).total_seconds()
    logger.info(f"Scheduling indexer for {next_index_run} (in {delay_index // 3600} hours and {(delay_index % 3600) // 60} minutes)")
    
    # Run indexer immediately
    logger.info("Starting indexer")
    run_indexer()

    # Schedule the next indexer run
    scheduler.enter(delay_index, 1, run_indexer)

    # Fetch known nodes
    response = requests.get(settings['URL'])
    if response.status_code == 200:
        data = json.loads(response.text)
        settings['known_nodes'].update(data)
    else:
        logger.error(f"Failed to download node list, status code {response.status_code}")
        return None

    # Run other tasks immediately and schedule them
    run_announcer()
    scheduler.enter(0, 1, run_announcer)
    
    run_heartbeat_checker()
    scheduler.enter(0, 1, run_heartbeat_checker)

def run_scheduler():
    while True:
        scheduler.run(blocking=False)
        time.sleep(1)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/global_search', methods=['POST'])
def global_search_route():
    conn = get_db_connection()
    query = request.form.get('query')
    category = request.form.get('category', None)
    if category == 'all':
        category = None
    
    results = search.global_search(query, settings['known_nodes'], settings['NODE_ID'], conn, "name", category)
    
    return render_template('results.html', query=query, category=category, results=results)

@app.route('/json/global_search', methods=['POST'])
def global_search_json():
    conn = get_db_connection()
    query = request.form.get('query')
    category = request.form.get('category', None)
    if category == 'all':
        category = None
    
    results = search.global_search(query, settings['known_nodes'], settings['NODE_ID'], conn, "name", category)
    
    return jsonify(results)

@app.route('/localsearch', methods=['POST'])
def localsearch_endpoint():
    conn = get_db_connection()
    data = request.get_json()

    search_term = data.get('search_term')
    search_type = data.get('search_type', 'name')
    category = data.get('category', None)

    logger.debug(f"Received request for local search: search_term={search_term}, search_type={search_type}, category={category}")

    matches = search.local_search(search_term, os.getenv('NODE_ID'), conn, search_type, category)

    return jsonify(matches), 200

@app.route('/md5_search/<md5_hash>')
def md5_search(md5_hash):
    conn = None
    try:
        conn = get_db_connection()  # Retrieve a connection from the pool
        results = search.global_search(md5_hash, settings['known_nodes'], settings['NODE_ID'], conn, "md5")
        return render_template('md5_results.html', md5_hash=md5_hash, results=results)
    except Exception as e:
        logger.error(f"Error during MD5 search: {e}")
        return "An error occurred during the search."
    finally:
        if conn:
            db_pool.putconn(conn)  # Return the connection to the pool after using it

@app.route('/json/md5_search/<md5_hash>')
def md5_search_json(md5_hash):
    conn = get_db_connection()
    return search.global_search(md5_hash, settings['known_nodes'], settings['NODE_ID'], conn, "md5")
    
@app.route('/download/<md5_hash>')
def download_file(md5_hash):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Select the file path based on the provided md5_hash
        select_query = """
        SELECT path FROM files WHERE md5_hash = %s;
        """
        cursor.execute(select_query, (md5_hash,))
        result = cursor.fetchone()
        
        if result:
            path = result[0]
            
            # Increment the download_count for the specific file
            update_query = """
            UPDATE files SET download_count = download_count + 1 WHERE md5_hash = %s;
            """
            cursor.execute(update_query, (md5_hash,))
            conn.commit()  # Commit the update
            
            return send_file(path)
        else:
            abort(404, description="File not found")
    
    finally:
        cursor.close()
        conn.close()

@app.route('/json/nodes')
def nodes():
    global settings
    return jsonify(list(settings["known_nodes"]))

@app.route('/total_file_size', methods=['GET'])
def total_file_size():
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT SUM(file_size) FROM files;")
            result = cursor.fetchone()
            total_size = result[0] if result[0] is not None else 0
            return jsonify({'total_file_size': total_size})
    except psycopg2.Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        connection.close()

initialize_settings()
threading.Thread(target=run_scheduler, daemon=True).start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv("NODE_PORT", 5000)))
