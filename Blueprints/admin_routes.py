import psycopg2
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from .compute_floyd import compute_floyd_warshall

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

# Create a Blueprint for the admin routes
admin_bp = Blueprint('admin', __name__, template_folder='templates', static_folder='static')


#################################################  Admin Signup Route  ###############################################################

@admin_bp.route('/admin_register', methods=['GET', 'POST'])
def admin_register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email').lower()
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash("Passwords do not match!", "danger")
            return redirect(url_for('admin.admin_register'))

        hashed_password = generate_password_hash(password) # Hash the password

        conn = get_db_connection()
        cur = conn.cursor()

        # Check if admin email already exists
        cur.execute("SELECT * FROM admin WHERE email = %s", (email,))
        existing_admin = cur.fetchone()

        if existing_admin:
            flash("Admin account already exists!", "warning")
            return redirect(url_for('admin.admin_register'))

        # Insert new admin
        cur.execute("INSERT INTO admin (name, email, password_hash) VALUES (%s, %s, %s)",
                    (name, email, hashed_password))
        conn.commit()
        cur.close()
        conn.close()

        flash("Admin registered successfully! Please log in.", "success")
        return redirect(url_for('admin.admin_login'))

    return render_template('admin_register.html')


#################################################   Admin Login Route   ############################################################3

@admin_bp.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form.get('email').lower()
        password = request.form.get('password')

        conn = get_db_connection()
        cur = conn.cursor()

        # Check admin email
        cur.execute("SELECT id, name , password_hash FROM admin WHERE email = %s", (email,))
        admin = cur.fetchone()

        if admin and check_password_hash(admin[2], password):
            session.clear()
            session['admin_id'] = admin[0]
            session['admin_name'] = admin[1]
            return redirect(url_for('admin.admin_dashboard'))
        
        flash("Invalid email or password!", "danger")

        cur.close()
        conn.close()

    return render_template('admin_login.html')


#####################################################  Admin Dashboard Route  #######################################################

# Function to get table sizes
def get_table_sizes():
    conn = get_db_connection()
    cursor = conn.cursor()
    table_names = ["shuttletoid", "stops", "bookings", "students"]
    
    table_sizes = {}
    for table in table_names:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        table_sizes[table] = cursor.fetchone()[0]
    
    cursor.close()
    conn.close()
    return table_sizes


@admin_bp.route('/admin_dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'student':
            return redirect(url_for('admin.student_management'))
        elif action == "booking":
            return redirect (url_for('admin.view_bookings'))
        elif action == "stop":
            return redirect(url_for('admin.stop_management'))
        else:
            return redirect(url_for('admin.shuttle_management'))
    

    else:
        table_sizes = get_table_sizes() # computing table sizes
        return render_template('admin_dashboard.html', table_sizes=table_sizes)
    

#####################################################  Student Management Route  ######################################################

@admin_bp.route('/student_management', methods=['GET', 'POST'])
def student_management():
    if request.method == 'POST':
        if 'enrollment_number' in request.form:  # Individual Student Points Assignment
            enrollment_number = request.form.get('enrollment_number').lower()
            points = request.form.get('points')

            if enrollment_number and points and points.isdigit():
                points = int(points)

                conn = get_db_connection()
                cur = conn.cursor()

                # Check if the student exists
                cur.execute("SELECT id FROM students WHERE email = %s;", (enrollment_number + "@bennett.edu.in",))
                student = cur.fetchone()

                if student:
                    cur.execute("UPDATE students SET points = points + %s WHERE email = %s;", 
                                (points, enrollment_number + "@bennett.edu.in"))
                    conn.commit()
                    flash(f'Successfully assigned {points} points to student {enrollment_number}!', 'success')
                else:
                    flash('Student not found!', 'danger')

                cur.close()
                conn.close()
            else:
                flash('Invalid input! Please enter a valid enrollment number and points.', 'danger')

        else:  # Bulk Points Assignment
            points_to_all = request.form.get('points')

            if points_to_all and points_to_all.isdigit():
                points_to_all = int(points_to_all)

                conn = get_db_connection()
                cur = conn.cursor()
                
                # Update all students' points
                cur.execute("UPDATE students SET points = points + %s;", (points_to_all,))
                conn.commit()
                
                cur.close()
                conn.close()
                
                flash(f'Successfully assigned {points_to_all} points to all students!', 'success')
            else:
                flash('Invalid input! Please enter a valid number.', 'danger')

        return redirect(url_for('admin.student_management'))

    return render_template('student_management.html')


#####################################################  Stop Management Route  #########################################################

@admin_bp.route('/stop_management', methods=['GET', 'POST'])
def stop_management():
    if request.method == 'POST':
        if 'stop_names' in request.form: # to add new stop
            stop_names = request.form.get('stop_names').split(',')  # gettig stop names by spliting along comma
            stop_names = [stop.strip() for stop in stop_names if stop.strip()]  # Remove extra spaces & empty values

            conn = get_db_connection()
            cur = conn.cursor()

            for stop_name in stop_names:
                cur.execute("SELECT id FROM stops WHERE name = %s;", (stop_name,))
                stop = cur.fetchone()

                if stop:
                    print("already exists")
                else:
                    cur.execute("INSERT INTO stops (name) VALUES (%s);", (stop_name,))
                    conn.commit()

            cur.close()
            conn.close()

        elif "completeForm" in request.form:    # to compute floyd_table and floyd_time
            compute_floyd_warshall()
            return redirect(url_for('admin.admin_dashboard'))

        else:   # to add new route
            conn = get_db_connection()
            cur = conn.cursor()
            stop_a = int(request.form.get('stop_a'))
            stop_b = int(request.form.get('stop_b'))
            points = int(request.form.get('points'))
            time = int(request.form.get('time'))
            cur.execute(
                "INSERT INTO route_matrix (stop_from, stop_to, points, time) VALUES (%s, %s, %s, %s) ON CONFLICT (stop_from, stop_to) DO NOTHING;",
                (stop_a, stop_b, points, time)
            )
            conn.commit()

        return redirect(url_for('admin.stop_management'))
    
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM stops;")
    stops = cur.fetchall()

    cur.execute("""
    SELECT sf.name AS stop_from, st.name AS stop_to, r.points, r.time 
    FROM route_matrix r
    JOIN stops sf ON r.stop_from = sf.id
    JOIN stops st ON r.stop_to = st.id;
""")
    routes = cur.fetchall()


    cur.close()
    conn.close()

    return render_template('stop_management.html', stops=stops , routes = routes)


#####################################################  View Bookings Made by students  ##################################################

@admin_bp.route('/view_bookings')
def view_bookings():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
            SELECT s.name AS shuttle_name, sf.name AS from_stop, st.name AS to_stop, b.booked_at::DATE AS date, b.booked_at::TIME AS time, student_id
            FROM bookings b
            JOIN shuttles s ON b.shuttle_id = s.id
            JOIN stops sf ON b.stop_from = sf.id
            JOIN stops st ON b.stop_to = st.id
            ORDER BY b.booked_at DESC;
        """)
    bookings = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('view_bookings.html', bookings = bookings)


#####################################################  Shuttle Management Route  ######################################################

@admin_bp.route('/shuttle_management', methods=['GET', 'POST'])
def shuttle_management():
    # Connect to the database
    conn = get_db_connection()
    cur = conn.cursor()
    
    if request.method == 'POST':
        # to add new shuttle
        if 'new_shuttle_name' in request.form:
            # Handle new shuttle creation
            new_shuttle_name = request.form.get('new_shuttle_name')
            
            try:
                # Insert new shuttle name
                cur.execute("INSERT INTO shuttletoid (name) VALUES (%s)", (new_shuttle_name,))
                
                conn.commit()
                flash('New shuttle added successfully!', 'success')
            except Exception as e:
                conn.rollback()
                flash(f'Error adding new shuttle: {str(e)}', 'error')
        else:
            # Handle main shuttle form submission
            shuttle_id = request.form.get('name')  # This will be the shuttle ID
            stop_sequence = request.form.getlist('stop_sequence[]')  # List of stop IDs
            date_str = request.form.get('date')
            time_str = request.form.get('time')
            capacity = request.form.get('capacity')
            
            try:
                # Convert stop_sequence to PostgreSQL array format
                stop_sequence_str = "{" + ",".join(stop_sequence) + "}"
                
                # Initialize occupancy array with zeros based on number of stops
                occupancy_str = "{" + ",".join(["0"] * len(stop_sequence)) + "}"
                
                # Get the shuttle name
                cur.execute("SELECT name FROM shuttletoid WHERE shuttle_id = %s", (shuttle_id,))
                shuttle_name = cur.fetchone()[0]
                
                # Insert new shuttle schedule
                cur.execute("""
                    INSERT INTO shuttles (name, stop_sequence, date, time, capacity, occupancy)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (shuttle_name, stop_sequence_str, date_str, time_str, capacity, occupancy_str))
                
                conn.commit()
                flash('Shuttle schedule added successfully!', 'success')
            except Exception as e:
                conn.rollback()
                flash(f'Error adding shuttle schedule: {str(e)}', 'error')
        
        # Redirect to avoid form resubmission
        return redirect(url_for('admin.shuttle_management'))
    
    # For GET requests, fetch data to populate the form
    try:
        # Get unique shuttle names
        cur.execute("SELECT shuttle_id, name FROM shuttletoid ORDER BY name")
        shuttles = [{"id": row[0], "name": row[1]} for row in cur.fetchall()]
        
        # Get all stops
        cur.execute("SELECT id, name FROM stops ORDER BY name")
        stops = [{"id": row[0], "name": row[1]} for row in cur.fetchall()]
        
    except Exception as e:
        flash(f'Error fetching data: {str(e)}', 'error')
        shuttles = []
        stops = []
    finally:
        cur.close()
        conn.close()
    
    return render_template('shuttle_management.html', shuttles=shuttles, stops=stops)


###################################################### Admin Logout Route ######################################################
@admin_bp.route('/admin_logout')
def admin_logout():
    session.clear()
    return redirect(url_for('landing_page'))