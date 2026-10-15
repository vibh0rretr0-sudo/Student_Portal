from flask import Flask, redirect, url_for
from app import create_app

app = create_app()

@app.route("/")
def index():
    from flask import session
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    role = session.get("role")
    if role == "student":
        return redirect(url_for("student.dashboard"))
    elif role == "professor":
        return redirect(url_for("professor.dashboard"))
    return redirect(url_for("auth.login"))

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
