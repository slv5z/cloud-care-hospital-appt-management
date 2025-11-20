# Hospital Management System

A web-based hospital management system built with FastAPI, designed to streamline patient, doctor, and administrative operations. This application allows patients to register, book appointments, and manage their healthcare needs, while doctors can view their schedules and patient information. Administrators have full control over system data, including managing patients, doctors, and appointments.

## Features

### Patient Dashboard
- Register as a new patient with OTP verification.
- View available doctors and search by specialization or name.
- Book appointments with doctors.
- View and cancel personal appointments (OTP required for security).

### Doctor Dashboard
- Secure login system.
- View assigned patients and their details.
- Search for patients by ID, name, or contact.
- View and manage appointments.

### Admin Dashboard
- Manage patients: Add, view, search, edit patient details.
- Manage doctors: Add, view, search, edit doctor information.
- Handle appointments: Book, view, cancel appointments.
- View cancelled appointments for auditing.

### General Features
- Role-based access control (Patient, Doctor, Admin).
- OTP-based authentication for patient actions.
- Responsive web interface using Jinja2 templates.
- Database integration with SQLAlchemy and MySQL.

## Technologies Used

- **Backend**: FastAPI (Python web framework)
- **Database**: MySQL with SQLAlchemy ORM
- **Frontend**: HTML/CSS with Jinja2 templating
- **Authentication**: Session-based with OTP for patients
- **Server**: Uvicorn ASGI server
- **Other**: Python-dotenv for environment variables

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/hospital-management-system.git
   cd hospital-management-system
   ```

2. **Create a virtual environment** (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up the database**:
   - Ensure MySQL is installed and running.
   - Create a database named `hospital_db`.
   - Update database connection details in `db.py` or use environment variables.

5. **Run database migrations** (if needed):
   - The application automatically creates tables on startup using SQLAlchemy.

## Usage

1. **Start the server**:
   ```bash
   uvicorn main:app --reload
   ```

2. **Access the application**:
   - Open your browser and go to `http://localhost:8000`
   - Select your role (Patient, Doctor, or Admin) from the role dashboard.

3. **Default Admin Credentials**:
   - Username: `admin`
   - Password: `pass123`

4. **Doctor Login**:
   - Use credentials created by admin.

## API Endpoints

### Role Selection
- `GET /` - Role dashboard
- `POST /select_role` - Select user role

### Patient Operations
- `GET /patient` - Patient dashboard
- `GET/POST /patient/add` - Register new patient
- `GET /patient/view_doctors` - View all doctors
- `GET /patient/search_doctors` - Search doctors
- `GET/POST /patient/book_appointment` - Book appointment
- `GET/POST /patient/view_appointments_auth` - View appointments (OTP required)
- `GET/POST /patient/cancel_appointment` - Cancel appointment

### Doctor Operations
- `GET /doctor/login` - Doctor login page
- `POST /doctor/login` - Authenticate doctor
- `GET /doctor/dashboard` - Doctor dashboard
- `GET /doctor/view_patients` - View patients
- `GET /doctor/search_patients` - Search patients
- `GET /doctor/view_appointments` - View appointments

### Admin Operations
- `GET /admin/login` - Admin login
- `POST /admin/login` - Authenticate admin
- `GET /admin` - Admin dashboard
- `GET/POST /admin/add_patient` - Add patient
- `GET /admin/view_patients` - View patients
- `GET/POST /admin/search_patients` - Search patients
- `GET/POST /admin/edit_patient` - Edit patient
- `GET/POST /admin/add_doctor` - Add doctor
- `GET /admin/view_doctors` - View doctors
- `GET/POST /admin/search_doctors` - Search doctors
- `GET/POST /admin/edit_doctor` - Edit doctor
- `GET/POST /admin/book_appointment` - Book appointment
- `GET /admin/view_appointments` - View appointments
- `GET/POST /admin/cancel_appointment` - Cancel appointment
- `GET /admin/view_cancelled` - View cancelled appointments

## Project Structure

```
hospital-management-system/
├── main.py                 # Main FastAPI application
├── models.py               # SQLAlchemy models
├── crud.py                 # CRUD operations
├── db.py                   # Database configuration
├── requirements.txt        # Python dependencies
├── static/                 # Static files (CSS, JS, images)
├── templates/              # Jinja2 HTML templates
│   ├── role_dashboard.html
│   ├── patient_dashboard.html
│   ├── doctor_dashboard.html
│   ├── admin_dashboard.html
│   └── ...
├── data/                   # Sample data files
└── README.md               # This file
```

## Contributing

1. Fork the repository.
2. Create a new branch for your feature (`git checkout -b feature/AmazingFeature`).
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`).
4. Push to the branch (`git push origin feature/AmazingFeature`).
5. Open a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact

If you have any questions or suggestions, feel free to open an issue or contact the maintainers.
