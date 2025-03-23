import psycopg2
from flask import session
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

def updateSession():
    conn = get_db_connection()
    cur = conn.cursor()

    dictpoint = []  # Store (point1, point2, weight(points))
    dicttime = []   # Store (point1, point2, time)

    cur.execute("SELECT * FROM floyd_route")
    edges = cur.fetchall()
    for edge in edges:
        dictpoint.append((edge[0], edge[1], edge[2]))  # (point1, point2, weight)
        dictpoint.append((edge[1], edge[0], edge[2]))  # Bidirectional storage

    cur.execute("SELECT * FROM floyd_time")
    edges = cur.fetchall()
    for edge in edges:
        dicttime.append((edge[0], edge[1], edge[2]))  # Store in dicttime
        dicttime.append((edge[1], edge[0], edge[2]))  # Bidirectional storage

    session['dictpoint'] = dictpoint  
    session['dicttime'] = dicttime    


    session['dictpoint'] = dictpoint  # Store as list of tuples
    session['dicttime'] = dicttime    # Store as list of tuples

    # Store stop names and IDs in session
    cur.execute("SELECT * FROM stops")
    stops = cur.fetchall()
    if stops:  
        for stop in stops:
            session[str(stop[1])] = stop[0]  # Store stop name → ID
            session[str(stop[0])] = stop[1]  # Store ID → stop name
    else:
        print("No stops found in the database!")
        

    cur.close()
    conn.close()
