# GymPro - Multi-Tenant Fitness Management Platform

GymPro is a comprehensive fitness management system designed for gym chains and fitness centers. It provides a complete solution for member management, trainer coordination, workout tracking, and real-time gym occupancy monitoring.

## Project Structure


372_proje/
├── backend/          # Flask REST API
├── frontend/         # Flutter Mobile Application
└── admin-panel/      # Web-based Admin Dashboard


## Features

### Multi-Tenant Architecture
- Single member account across multiple gyms
- Gym-specific trainers, programs, and settings
- Centralized member data with per-gym memberships

### Member Features
- Registration and authentication
- Multiple gym memberships (timed or credit-based)
- Real-time gym occupancy view from home
- QR code-based turnstile entry/exit
- Custom workout routines
- Pre-built workout programs
- Trainer profiles and ratings

### Admin Panel Features
- Member management
- Trainer management
- Exercise database
- Fixed workout programs (CRUD)
- Gym capacity and settings

### Turnstile System
- QR code scanning for gym entry/exit
- Real-time occupancy tracking
- Member and trainer access control

## Technology Stack

### Backend
- *Framework*: Flask (Python)
- *Database*: MySQL with ODBC connectivity
- *API*: RESTful JSON API
- *CORS*: Enabled for cross-origin requests

### Mobile App
- *Framework*: Flutter (Dart)
- *State Management*: Provider
- *Navigation*: GoRouter
- *UI*: Custom dark theme with gradient cards

### Admin Panel
- *Frontend*: HTML, CSS (Tailwind + Bootstrap)
- *JavaScript*: Vanilla JS with Fetch API

## Database Schema

The system uses 11 tables with proper foreign key relationships:

| Table | Description |
|-------|-------------|
| Gym | Fitness center locations |
| Member | Global user accounts |
| Membership | Member-Gym relationships (multi-tenancy) |
| Trainer | Gym-specific trainers |
| GymAdmin | Admin accounts per gym |
| TurnstileEvent | Entry/exit logs |
| Exercise | Exercise database |
| FixedWorkout | Pre-built workout programs |
| FixedWorkoutExercise | Program-exercise mappings |
| CustomRoutine | User-created routines |
| CustomRoutineExercise | Routine-exercise mappings |

### Database Views
- ActiveMembersView
- TrainersInGymView
- GymStatsView
- TodayEntriesView
- MemberWorkoutSummaryView

### Indexes
Optimized indexes for common queries on member_id, gym_id, and date fields.

## Installation

### Prerequisites
- Python 3.8+
- MySQL 8.0+
- MySQL ODBC Driver 9.5
- Flutter SDK 3.0+
- Node.js (optional, for admin panel development)

### Backend Setup

1. Navigate to backend directory:
   bash
   cd backend
   

2. Install Python dependencies:
   bash
   pip install flask flask-cors pyodbc
   

3. Create the database:
   bash
   mysql -u root -p < createDB.sql
   

4. (Optional) Populate sample data:
   bash
   python populate_saas.py
   

5. Run the server:
   bash
   python app.py
   

The API will be available at http://localhost:5000.

### Mobile App Setup

1. Navigate to frontend directory:
   bash
   cd frontend
   

2. Get Flutter packages:
   bash
   flutter pub get
   

3. Run the app:
   bash
   flutter run
   

### Admin Panel

Open admin-panel/index.html in a web browser, or serve it with a local server.

## API Endpoints

### Authentication
- POST /api/register - User registration
- POST /api/login - User login

### Gyms
- GET /api/my-gyms - List user's gym memberships with occupancy
- GET /api/gym/<id>/dashboard - Gym dashboard data

### Turnstile
- POST /api/turnstile/checkin - QR-based gym entry
- POST /api/turnstile/checkout - QR-based gym exit

### Workouts
- GET /api/fixed-workouts - List workout programs
- GET /api/exercises - List exercises
- POST /api/my-routines - Create custom routine
- DELETE /api/my-routines/<id>/exercises/<eid> - Remove exercise from routine

### Admin
- GET/POST/PUT/DELETE /api/admin/programs - Program CRUD
- GET/POST/PUT/DELETE /api/admin/exercises - Exercise CRUD
- GET/POST/PUT/DELETE /api/admin/trainers - Trainer CRUD

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| DB_HOST | 127.0.0.1 | MySQL server host |
| DB_NAME | gympro_db | Database name |
| DB_USER | root | Database user |
| DB_PASSWORD | - | Database password |

## License

This project is developed for educational purposes.

## Contributors

Developed as part of CENG 372 Database Management Systems course project.
