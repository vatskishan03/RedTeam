import { Agent, TimelineStep } from './types';

export const AGENTS: Record<string, Agent> = {
  attacker: {
    id: 'attacker',
    name: 'Red Team Attacker',
    role: 'Finds vulnerabilities & creates exploits',
    icon: '🔴',
    color: '#f85149',
    colorClass: 'text-agent-attacker',
    glowClass: 'attacker',
  },
  defender: {
    id: 'defender',
    name: 'Blue Team Defender',
    role: 'Proposes secure fixes',
    icon: '🟢',
    color: '#3fb950',
    colorClass: 'text-agent-defender',
    glowClass: 'defender',
  },
  arbiter: {
    id: 'arbiter',
    name: 'Security Arbiter',
    role: 'Validates fixes & makes verdicts',
    icon: '⚖️',
    color: '#d29922',
    colorClass: 'text-agent-arbiter',
    glowClass: 'arbiter',
  },
  reporter: {
    id: 'reporter',
    name: 'Security Reporter',
    role: 'Generates audit report',
    icon: '📋',
    color: '#58a6ff',
    colorClass: 'text-agent-reporter',
    glowClass: 'reporter',
  },
};

export const TIMELINE_STEPS: TimelineStep[] = [
  { id: 'scan', label: 'Scanning', status: 'pending', agent: 'attacker' },
  { id: 'vulns', label: 'Vulns Found', status: 'pending', agent: 'attacker' },
  { id: 'fix', label: 'Fix Proposed', status: 'pending', agent: 'defender' },
  { id: 'reattack', label: 'Re-Attack', status: 'pending', agent: 'attacker' },
  { id: 'verdict', label: 'Verdict', status: 'pending', agent: 'arbiter' },
  { id: 'report', label: 'Report', status: 'pending', agent: 'reporter' },
];

export const SAMPLE_VULNERABLE_CODE = {
  python_sql: `# Example: SQL Injection Vulnerability
def get_user(username):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    # VULNERABLE: String concatenation in SQL query
    query = f"SELECT * FROM users WHERE username = '{username}'"
    cursor.execute(query)
    return cursor.fetchone()

def login(request):
    username = request.form['username']
    password = request.form['password']
    user = get_user(username)
    if user and user.password == password:
        return "Login successful"
    return "Invalid credentials"`,

  python_xss: `# Example: XSS Vulnerability
from flask import Flask, request

app = Flask(__name__)

@app.route('/greet')
def greet():
    name = request.args.get('name', 'Guest')
    # VULNERABLE: Unescaped user input in HTML
    return f"<h1>Welcome, {name}!</h1>"

@app.route('/search')
def search():
    query = request.args.get('q', '')
    # VULNERABLE: Reflected XSS
    return f"<p>Results for: {query}</p>"`,

  python_path: `# Example: Path Traversal Vulnerability
import os

def read_document(filename):
    # VULNERABLE: No path validation
    doc_path = f"/app/documents/{filename}"
    with open(doc_path, 'r') as f:
        return f.read()

def download_file(user_input):
    # VULNERABLE: Path traversal possible
    base_dir = "/var/uploads/"
    file_path = base_dir + user_input
    return open(file_path, 'rb').read()`,

  javascript_xss: `// Example: DOM-based XSS
function displayUserInput() {
  const params = new URLSearchParams(window.location.search);
  const name = params.get('name');
  
  // VULNERABLE: innerHTML with user input
  document.getElementById('greeting').innerHTML = 
    '<h1>Hello, ' + name + '!</h1>';
}

function searchResults(query) {
  // VULNERABLE: Document.write with user input
  document.write('<p>Searching for: ' + query + '</p>');
}`,
};

export const SEVERITY_COLORS = {
  critical: {
    bg: 'bg-red-500',
    text: 'text-white',
    border: 'border-red-500',
  },
  high: {
    bg: 'bg-orange-500',
    text: 'text-white',
    border: 'border-orange-500',
  },
  medium: {
    bg: 'bg-yellow-500',
    text: 'text-black',
    border: 'border-yellow-500',
  },
  low: {
    bg: 'bg-green-500',
    text: 'text-black',
    border: 'border-green-500',
  },
};
