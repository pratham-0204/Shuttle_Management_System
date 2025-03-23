import psycopg2
from flask import redirect, url_for, render_template, request, Blueprint, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from .getShuttles import getShuttles
from .updateSessions import updateSession
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_db_connection():
    return psycopg2.connect(
        dbname=os.environ.get("DB_NAME"),
        user=os.environ.get("DB_USER"),
        password=os.environ.get("DB_PASSWORD"),
        host=os.environ.get("DB_HOST"),
        port=os.environ.get("DB_PORT")
    )

# Blueprint Configuration
student_bp = Blueprint('student', __name__, template_folder='templates', static_folder='static')


##################################################### Student Registration Route #####################################################

@student_bp.route('/student_register', methods=['GET', 'POST'])
def student_register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = (request.form.get('email')).lower()
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash("Passwords do not match!", "danger")
            return redirect(url_for('student.student_register'))

        hashed_password = generate_password_hash(password) # Hash the password

        conn = get_db_connection()
        cur = conn.cursor()

        # Check if email already exists
        cur.execute("SELECT * FROM students WHERE email = %s", (email,))
        existing_user = cur.fetchone()

        if existing_user:
            flash("Account already exists with this email!", "warning")
            return redirect(url_for('student.student_register'))

        # Insert new user
        cur.execute("INSERT INTO students (name, email, password_hash) VALUES (%s, %s, %s)",
                    (name, email, hashed_password))
        conn.commit()
        cur.close()
        conn.close()

        flash("Registration successful! You can now log in.", "success")
        return redirect(url_for('student.student_login'))

    return render_template('student_register.html')


###################################################### Student Login Route ##########################################################

@student_bp.route('/student_login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        email = request.form.get('email').lower() # Convert email to lowercase
        password = request.form.get('password')

        conn = get_db_connection()
        cur = conn.cursor()

        # Fetch student ID and password hash from the DB
        cur.execute("SELECT id, name, password_hash, points FROM students WHERE email = %s", (email,))
        user = cur.fetchone()

        if user:
            student_id = user[0]
            stored_hash = user[2]  # Unpacking tuple
            if check_password_hash(stored_hash, password):  # Validate password
                session.clear()
                # Store student ID in session
                session['student_id'] = student_id
                session['student_name'] = user[1]
                session['points'] = user[3]
                return redirect(url_for("student.student_dashboard"))  

        flash("Invalid email or password!", "danger")

        cur.close()
        conn.close()

    return render_template('student_login.html')



###################################################### Student Dashboard Route ##########################################################

@student_bp.route('/student_dashboard', methods=['GET', 'POST'])
def student_dashboard():
    if request.method == "POST":
        from_stop = request.form.get('from_stop')
        to_stop = request.form.get('to_stop')
        date_chosen = request.form.get('date')

        return redirect(url_for('student.find_shuttle' , from_stop=from_stop, to_stop=to_stop, date_chosen=date_chosen)) # Redirect to find_shuttle route

    
    else:
        conn = get_db_connection()
        cur = conn.cursor()

        updateSession() # updating the session with the floyd route data and floyd time data

        # Fetch available stops
        cur.execute("SELECT id, name FROM stops ORDER BY name;")
        stops = cur.fetchall()

        # Fetch upcoming bookings (today or future)
        cur.execute("""
            SELECT s.name AS shuttle_name, sf.name AS from_stop, st.name AS to_stop, b.booked_at::DATE AS date, b.booked_at::TIME AS time
            FROM bookings b
            JOIN shuttles s ON b.shuttle_id = s.id
            JOIN stops sf ON b.stop_from = sf.id
            JOIN stops st ON b.stop_to = st.id
            WHERE b.student_id = %s
            ORDER BY b.booked_at DESC;
        """, (session['student_id'],))
        bookings = cur.fetchall()

        cur.close()
        conn.close()

        return render_template('student_dashboard.html', stops=stops, bookings=bookings)  


###################################################### Find Shuttle Route ##########################################################3    

@student_bp.route('/find_shuttle', methods=['GET', 'POST'])
def find_shuttle():
    from_stop = request.args.get('from_stop')
    to_stop = request.args.get('to_stop')
    date_chosen = request.args.get('date_chosen')

    if request.method == "POST":
        shuttle_id = request.form.get("shuttle_id")
        from_stop = request.form.get("from_stop")
        to_stop = request.form.get("to_stop")
        date_chosen = request.form.get("date_chosen")
        pointsTodeduct = request.form.get("points") 

        conn = get_db_connection()
        cur = conn.cursor()

        # Check if there are enough points
        if int(pointsTodeduct) > session['points']:
            flash("Insufficient points to book this shuttle!", "danger")
            return redirect(url_for('student.student_dashboard'))

        session['points'] -= int(pointsTodeduct) # Deduct points from student's account
        cur.execute("UPDATE students SET points = %s WHERE id = %s", (session['points'], session['student_id'])) # Update points in DB
        conn.commit()

        cur.execute("INSERT INTO bookings (student_id, shuttle_id, stop_from, stop_to) VALUES (%s, %s, %s, %s)", # Insert booking record
                    (session['student_id'], shuttle_id, from_stop, to_stop))
        conn.commit()

        cur.execute("select * from shuttles where id = %s", (shuttle_id,)) # Update shuttle occupancy (used to compute prefix sum)
        shuttle = cur.fetchone()

        List = shuttle[-1] # List of occupancy
        List[shuttle[2].index(int(from_stop))] += 1 # Increment occupancy at from_stop
        List[shuttle[2].index(int(to_stop))] -= 1

        cur.execute("UPDATE shuttles SET occupancy = %s WHERE id = %s", (List, shuttle_id))
        conn.commit()

        cur.close()
        conn.close()
        
        # Flash success message
        flash("Shuttle booked successfully!", "success")
        return redirect(url_for('student.student_dashboard'))
    
    else:
        conn = get_db_connection()
        cur = conn.cursor()
        pointsTodeduct = 0

        for point1, point2, weight in session['dictpoint']:
            if ((int(from_stop) == point1 and int(to_stop) == point2) or (int(from_stop) == point2 and int(to_stop) == point1)):
                pointsTodeduct = int(weight)
                break

        # Check if there are enough points , the message will be flashed in the dashboard
        if(pointsTodeduct > session['points']):
            flash("Insufficient points! You need " + str(pointsTodeduct) + " points for this route.", "danger")
            return redirect(url_for('student.student_dashboard'))
        
        # Check if the route is valid, possibly the starting and destination points are same
        if(pointsTodeduct == 0):
            flash("Invalid Route! Please select a valid route.", "danger")
            return redirect(url_for('student.student_dashboard'))
        
        # there is route between the staring and destination points
        if(pointsTodeduct < 0):
            flash("There is no route between these points", "danger")
            return redirect(url_for('student.student_dashboard'))
        
        cur.close()
        conn.close()

        ShuttlesList = getShuttles(from_stop, to_stop, date_chosen) # id, name, availability , route, start_time, end_time

        return render_template('find_shuttle.html', shuttle_list=ShuttlesList, from_stop=from_stop, to_stop=to_stop, pointsTodeduct=pointsTodeduct, date=date_chosen)
    

################################################# student logout ##############################################################

@student_bp.route("/student_logout")
def student_logout():
    session.clear()
    return redirect(url_for('landing_page'))

