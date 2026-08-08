# Campus Interview Managing System

A modern, robust web application designed to streamline the campus recruitment and placement process. This system serves as a bridge between students, placement officers, and recruiting companies, offering a premium dark glassmorphism interface.

## Features

- **Student Portal:**
  - Secure Registration & Login
  - Dashboard with realtime application status
  - Apply for active placement drives
  - Profile Management
  - Access to placement preparation resources
  - Support ticket system
- **Admin Dashboard (Placement Officer):**
  - KPI Analytics (Total Users, Placement Requests, Companies)
  - Manage student records and job applications
  - System logs and login history
  - Support ticket resolution
  - Broadcast notifications

## Technologies Used

- **Backend:** Python, Flask, Flask-MySQLdb, Flask-Session
- **Database:** MySQL
- **Frontend:** HTML5, CSS3 (Custom Dark Glassmorphism Theme), FontAwesome
- **Styling:** CSS variables, backdrop-filters (blur), responsive flexbox/grid layouts

## Setup and Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up the MySQL database and import your schema.
4. Update the database configuration in `app.py`.
5. Run the application:
   ```bash
   python app.py
   ```

## Design

The application features a modern "dark glassmorphism" UI with deep gradient backgrounds, translucent panels with blur effects, interactive hover states, and smooth transitions for a premium user experience.
