import psycopg2
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

def compute_floyd_warshall():
    """
    Computes shortest paths using Floyd-Warshall and updates floyd_route & floyd_time tables.
    Uses get_db_connection() to connect to the database.
    """
    try:
        # Connect to PostgreSQL
        conn = get_db_connection()
        cur = conn.cursor()

        # Get all stop IDs
        cur.execute("SELECT id FROM stops;")
        stops = [row[0] for row in cur.fetchall()]
        n = len(stops)
        INF = float('inf')

        # Map stop IDs to matrix indices
        stop_index = {stop: i for i, stop in enumerate(stops)}
        index_stop = {i: stop for stop, i in stop_index.items()}

        # Initialize matrices
        dist_points = [[INF] * n for _ in range(n)]
        dist_time = [[INF] * n for _ in range(n)]

        # Fill matrices with direct routes from route_matrix (UNDIRECTED)
        cur.execute("SELECT stop_from, stop_to, points, time FROM route_matrix;")
        for stop_from, stop_to, points, time in cur.fetchall():
            i, j = stop_index[stop_from], stop_index[stop_to]
            dist_points[i][j] = dist_points[j][i] = points  # Undirected
            dist_time[i][j] = dist_time[j][i] = time  # Undirected

        # Set self-distances to 0
        for i in range(n):
            dist_points[i][i] = 0
            dist_time[i][i] = 0

        # Floyd-Warshall Algorithm
        for k in range(n):
            for i in range(n):
                for j in range(n):
                    dist_points[i][j] = min(dist_points[i][j], dist_points[i][k] + dist_points[k][j])
                    dist_time[i][j] = min(dist_time[i][j], dist_time[i][k] + dist_time[k][j])

        # Clear existing data in floyd_route & floyd_time
        cur.execute("DELETE FROM floyd_route;")
        cur.execute("DELETE FROM floyd_time;")

        # Insert results (only store i → j where i < j)
        for i in range(n):
            for j in range(i + 1, n):
                point1, point2 = index_stop[i], index_stop[j]
                weight = dist_points[i][j] if dist_points[i][j] != INF else -1
                weight_time = dist_time[i][j] if dist_time[i][j] != INF else -1

                cur.execute("INSERT INTO floyd_route (point1, point2, weight) VALUES (%s, %s, %s);",
                            (point1, point2, weight))

                cur.execute("INSERT INTO floyd_time (point1, point2, weight_time) VALUES (%s, %s, %s);",
                            (point1, point2, weight_time))

        # Commit changes
        conn.commit()
        print("Floyd-Warshall computation completed and stored in database.")

    except Exception as e:
        print(f"Error: {e}")

    finally:
        # Close connection
        cur.close()
        conn.close()

