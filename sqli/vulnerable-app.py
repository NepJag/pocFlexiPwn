from flask import Flask, request, render_template_string, jsonify
import sqlite3
import json
import logging
from datetime import datetime

app = Flask(__name__)

# Configurar logging estructurado (estilo SIGMA)
logging.basicConfig(
    filename='/tmp/webapp.log',
    level=logging.INFO,
    format='%(message)s'  # Solo el mensaje JSON
)

def log_event(event_type, details):
    """Registra eventos en formato JSON estructurado"""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "event_type": event_type,
        "source": "vulnerable_webapp",
        **details
    }
    logging.info(json.dumps(log_entry))

# Inicializar DB
def init_db():
    conn = sqlite3.connect('/tmp/users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY, username TEXT, password TEXT, role TEXT)''')
    c.execute("DELETE FROM users")  # Limpiar
    c.execute("INSERT INTO users VALUES (1, 'admin', 'admin123', 'admin')")
    c.execute("INSERT INTO users VALUES (2, 'user', 'user123', 'user')")
    conn.commit()
    conn.close()

init_db()

LOGIN_PAGE = '''
<!DOCTYPE html>
<html>
<head><title>Login</title></head>
<body>
    <h1>Login Page</h1>
    <form method="POST" action="/login">
        <input type="text" name="username" placeholder="Username"><br>
        <input type="password" name="password" placeholder="Password"><br>
        <button type="submit">Login</button>
    </form>
    {% if message %}
    <p style="color: {% if success %}green{% else %}red{% endif %}">{{ message }}</p>
    {% endif %}
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(LOGIN_PAGE)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    
    # Log del intento de login
    log_event("authentication_attempt", {
        "username": username,
        "source_ip": request.remote_addr,
        "user_agent": request.headers.get('User-Agent')
    })
    
    # VULNERABILIDAD INTENCIONAL: SQL Injection
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    
    # Log de la query ejecutada (detección!)
    log_event("database_query", {
        "query": query,
        "username": username,
        "suspicious_chars": any(c in username + password for c in ["'", '"', '--', ';', 'OR', 'or'])
    })
    
    try:
        conn = sqlite3.connect('/tmp/users.db')
        c = conn.cursor()
        c.execute(query)
        result = c.fetchone()
        conn.close()
        
        if result:
            # Login exitoso
            log_event("authentication_success", {
                "username": username,
                "user_id": result[0],
                "role": result[3],
                "method": "sqli" if "'" in username or "'" in password else "normal"
            })
            
            return render_template_string(LOGIN_PAGE, 
                message=f"Bienvenido {result[1]}! Rol: {result[3]}",
                success=True)
        else:
            log_event("authentication_failure", {
                "username": username,
                "reason": "invalid_credentials"
            })
            return render_template_string(LOGIN_PAGE, 
                message="Credenciales invádidas.",
                success=False)
                
    except sqlite3.Error as e:
        # Log de error SQL (SQLi fail)
        log_event("database_error", {
            "query": query,
            "error": str(e),
            "likely_sqli_attempt": True
        })
        return render_template_string(LOGIN_PAGE, 
            message=f"Database error: {e}", 
            success=False)

if __name__ == '__main__':
    print("App vulnerable corriendo en http://localhost:5000")
    app.run(debug=True, port=5000)