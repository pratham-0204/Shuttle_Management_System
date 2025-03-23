import psycopg2
from flask import session
from datetime import datetime, timedelta
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

# Check if the sequence is valid from `from_stop` to `to_stop` means `from_stop` comes before `to_stop`
def checkSequence(l, from_stop, to_stop):
    if from_stop not in l or to_stop not in l:
        return False
    return l.index(from_stop) < l.index(to_stop)


# Check the availability of seats in the shuttle using prefix sum technique
def checkAvailability(prefixlist, from_stop, to_stop, capacity, sequencelist):
    if from_stop not in sequencelist or to_stop not in sequencelist:
        return -1

    sum = 0
    templist = []
    
    for i in prefixlist:
        sum += i
        templist.append(sum)

    maxx = 0
    for i in range(sequencelist.index(from_stop), sequencelist.index(to_stop) ):
        if templist[i] >= capacity:
            return -1
        maxx = max(maxx, templist[i])
    
    return maxx # Return the maximum number of seats occupied in the shuttle between `from_stop` and `to_stop`


# Get the route sequence from `from_stop` to `to_stop`
def getrouteSequence(l, from_stop, to_stop):
    s = ""
    for i in range(l.index(from_stop), l.index(to_stop) + 1):
        s += str(session.get(str(l[i]), l[i])) + " --> "
    return s[:-4]  # Remove the last arrow


# Get the start time of the shuttle from `from_stop` as we only have the start time of the shuttle
# We need to calculate the start time of the shuttle from `from_stop`
def getStartTime(l, from_stop, shuttle_start_time):
    if from_stop == l[0]:
        return shuttle_start_time

    sum_time = 0  
    for i in range(len(l) - 1):  
        for point1, point2, weight in session.get('dicttime', []):
            if (point1 == l[i] and point2 == l[i + 1]) or (point1 == l[i + 1] and point2 == l[i]):
                sum_time += weight
                break  
        if l[i + 1] == from_stop:
            break  

    # Convert shuttle_start_time (datetime.time) to datetime and add minutes
    start_time = datetime.combine(datetime.today(), shuttle_start_time) + timedelta(minutes=sum_time + l.index(from_stop) * 2 - 2) # 2 minutes stoppage time at each stop
    return start_time.time()  # Return only the time part


# Get the end time of the shuttle at `to_stop` as we only have the start time of the shuttle
def getEndTime(l, to_stop, shuttle_start_time):
    sum_time = 0
    for i in range(len(l) - 1):  
        for point1, point2, weight in session.get('dicttime', []):
            if (point1 == l[i] and point2 == l[i + 1]) or (point1 == l[i + 1] and point2 == l[i]):
                sum_time += weight
                break  
        if l[i + 1] == to_stop:
            break  

    # Convert shuttle_start_time (datetime.time) to datetime and add minutes
    end_time = datetime.combine(datetime.today(), shuttle_start_time) + timedelta(minutes=sum_time + l.index(to_stop) * 2 - 2) # 2 minutes stoppage time at each stop
    return end_time.time()  # Return only the time part


# Get the shuttles from `from_stop` to `to_stop` on `date_chosen`
def getShuttles(from_stop, to_stop, date_chosen):
    from_stop = int(from_stop)
    to_stop = int(to_stop)

    conn = get_db_connection()
    cur = conn.cursor()

    # Ensure `date_chosen` is in proper format (YYYY-MM-DD)
    cur.execute("SELECT * FROM shuttles WHERE date = %s;", (date_chosen,))
    shuttles = cur.fetchall()

    cur.close()
    conn.close()

    finalShuttles = []
    for shuttle in shuttles:
        availability = checkAvailability(shuttle[-1], from_stop, to_stop, shuttle[-2], shuttle[2]) # Check availability of seats

        if checkSequence(shuttle[2], from_stop, to_stop) and availability != -1: # Check if the sequence is valid and seats are available , -1 means no seats available

            finalShuttles.append([
                shuttle[0],  # Shuttle ID
                shuttle[1],  # Shuttle Name
                shuttle[-2] - availability,  # Remaining seats
                getrouteSequence(shuttle[2], from_stop, to_stop),  # Route sequence
                getStartTime(shuttle[2], from_stop, shuttle[4]),  # Start time
                getEndTime(shuttle[2], to_stop, shuttle[4])  # End time
            ])

    return finalShuttles # Return the list of shuttles from `from_stop` to `to_stop` on `date_chosen`
