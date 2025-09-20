from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from db import get_pending_requests, get_all_requests, resolve_request, is_timed_out

app = Flask(__name__)
app.secret_key = "super_secret_key"  # For flash messages

@app.route('/')
def index():
    pending = get_pending_requests()
    history = get_all_requests()
    history_with_status = []
    for req in history:
        status = req[3]
        if status == 'pending' and is_timed_out(req[5]):
            status = 'unresolved'
        history_with_status.append(list(req) + [status])
    conn = sqlite3.connect('db.sqlite')
    c = conn.cursor()
    c.execute("SELECT question, answer FROM knowledge")
    kb = c.fetchall()
    conn.close()
    return render_template('index.html', pending=pending, history=history_with_status, kb=kb)

@app.route('/resolve/<int:request_id>', methods=['GET', 'POST'])
def resolve(request_id):
    conn = sqlite3.connect('db.sqlite')
    c = conn.cursor()
    c.execute("SELECT * FROM help_requests WHERE id = ?", (request_id,))
    req = c.fetchone()
    conn.close()
    if not req:
        flash("Request not found", "error")
        return redirect(url_for('index'))
    if request.method == 'POST':
        answer = request.form.get('answer', '').strip()
        if not answer:
            flash("Answer cannot be empty", "error")
            return render_template('resolve.html', req=req)
        question = req[1]
        resolve_request(request_id, answer, question)
        flash(f"Request #{request_id} resolved successfully", "success")
        return redirect(url_for('index'))
    return render_template('resolve.html', req=req)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == "__main__":
    app.run(debug=True, port=5000)