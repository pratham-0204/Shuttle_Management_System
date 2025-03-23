import os
from flask import Flask, redirect, url_for, render_template, request, session
from Blueprints.student_routes import student_bp  # Import Student Blueprint
from Blueprints.admin_routes import admin_bp  # Import Admin Blueprint

app = Flask(__name__)
# Registering Blueprints
app.register_blueprint(student_bp, url_prefix='/student')
app.register_blueprint(admin_bp, url_prefix='/admin')

# Secret Key for session
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))

@app.route('/', methods=["GET", "POST"])
def landing_page():
    if request.method == "POST":
        action = request.form["action"]
        if action == "student":
            return redirect(url_for('student.student_login')) # Redirect to student login
        else:
            return redirect(url_for('admin.admin_login'))  # Redirect to admin login
    return render_template('landing.html') # Render landing page



if __name__ == '__main__':
    app.run(debug=True)
