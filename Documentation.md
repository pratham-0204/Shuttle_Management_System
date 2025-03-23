# Blitz (Shuttle Management System)

## Overview

The **Shuttle Management System** is designed to efficiently manage shuttle services within a university campus. It allows students to book shuttles based on predefined routes while ensuring optimal seat allocation and fare calculation.

## Features

- **Multi-Route Management:** Admins can define shuttle routes with multiple stops.
- **Student Profiles:** Students can register, log in, and manage their bookings.
- **Digital Fare Management:** Points are deducted based on the shortest path between stops using the Floyd-Warshall algorithm.
- **Smart Shuttle Booking:** Students can book shuttles dynamically based on seat availability.
- **Trip History Tracking:** Students can view past bookings.
- **Seat Availability Calculation:** Uses a **Prefix Sum** approach to determine the number of available seats between any two stops.

## Technologies Used

- **Backend:** Flask (Python)
- **Database:** PostgreSQL (Hosted on Aiven)
- **Algorithm:** Floyd-Warshall Algorithm (for path's fare and time calculation) , prefix sum(for calculation of point to point seat availability)
- **Frontend:** HTML, CSS, Bootstrap

## Database Schema

### Students Table

Stores student details.

```sql
CREATE TABLE students (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    points INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Admin Table

Stores admin details.

```sql
CREATE TABLE admin (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL
);
```

### Stops Table

Stores all available shuttle stops.

```sql
CREATE TABLE stops (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL  
);
```

### Route Matrix Table

Stores the weights (points and time) between stops for Floyd-Warshall calculations.

```sql
CREATE TABLE route_matrix (
    id SERIAL PRIMARY KEY,
    stop_from INT REFERENCES stops(id) ON DELETE CASCADE,
    stop_to INT REFERENCES stops(id) ON DELETE CASCADE,
    points INT NOT NULL,
    time INT,
    UNIQUE(stop_from, stop_to)
);
```

### Bookings Table

Stores all bookings made by students.

```sql
CREATE TABLE bookings (
    id SERIAL PRIMARY KEY,
    student_id INT REFERENCES students(id) ON DELETE CASCADE,
    shuttle_id INT REFERENCES shuttles(id) ON DELETE CASCADE,
    stop_from INT REFERENCES stops(id) ON DELETE CASCADE,
    stop_to INT REFERENCES stops(id) ON DELETE CASCADE,
    booked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Shuttles Table

Stores shuttle details including routes and occupancy.

```sql
CREATE TABLE shuttles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    stop_sequence INT[] NOT NULL,
    date DATE NOT NULL,
    time TIME NOT NULL,
    capacity INT NOT NULL,
    occupancy INT[] NOT NULL
);
```

### Floyd-Warshall Output Tables

Stores precomputed shortest paths and times.

```sql
CREATE TABLE floyd_route (
    point1 INT NOT NULL,
    point2 INT NOT NULL,
    weight INT NOT NULL
);

CREATE TABLE floyd_time (
    point1 INT NOT NULL,
    point2 INT NOT NULL,
    weight_time INT NOT NULL
);
```

### Shuttle to ID Table

Maps shuttle names to unique IDs.

```sql
CREATE TABLE shuttletoid (
    shuttle_id INT,
    name VARCHAR
);
```

## Algorithms Used

1. **Floyd-Warshall Algorithm**: Used to compute the shortest path and time between all pairs of stops, allowing for efficient fare calculation.
2. **Prefix Sum Approach**: Used to determine seat availability dynamically between any two stops along a shuttle’s route.

## How it Works

1. **Admin Setup:** The admin defines all stops and assigns shuttle routes.
2. **Path Computation:** Floyd-Warshall algorithm precomputes shortest paths and time matrices.
3. **Shuttle Booking:** Students request shuttles, and seat availability is determined using the Prefix Sum approach.
4. **Fare Calculation:** The system deducts points based on the shortest route between selected stops.

## Future Enhancements

- Implement real-time GPS tracking for shuttles.
- Introduce mobile push notifications for booking reminders.
- Integrate payment gateways for fare top-ups.


