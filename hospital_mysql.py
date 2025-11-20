#!/usr/bin/env python3
"""
hospital_mysql.py
CLI Hospital Appointment Management System using MySQL backend.
Requires: mysql-connector-python, python-dotenv (optional)
"""

import os
import csv
import mysql.connector
from pathlib import Path
from datetime import datetime
from mysql.connector import Error
from dotenv import load_dotenv
import random

# Load .env if present
load_dotenv()

# ---------------- Database configuration ----------------
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "hospital_app")      # change if necessary
DB_PASS = os.getenv("DB_PASS", "pass@123")          # change to your password
DB_NAME = os.getenv("DB_NAME", "hospital_db")
DB_PORT = int(os.getenv("DB_PORT", 3306))

# ---------------- Helper Functions ----------------
def get_db_connection():
    """Return a new DB connection. Caller must close it."""
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASS,
            database=DB_NAME,
            port=DB_PORT,
            autocommit=False
        )
        return conn
    except Error as e:
        print(f"[DB Error] Could not connect to database: {e}")
        raise

def initialize_db():
    """Create tables if they do not exist."""
    ddl_patients = """
    CREATE TABLE IF NOT EXISTS patients (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        age INT,
        gender VARCHAR(20),
        dob DATE,
        contact VARCHAR(20) UNIQUE,
        symptoms VARCHAR(255),
        otp_code VARCHAR(10)
    ) ENGINE=InnoDB;
    """
    ddl_doctors = """
    CREATE TABLE IF NOT EXISTS doctors (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        specialization VARCHAR(100),
        username VARCHAR(50) UNIQUE,
        password VARCHAR(50)

    ) ENGINE=InnoDB;
    """
    ddl_appointments = """
    CREATE TABLE IF NOT EXISTS appointments (
         id INT AUTO_INCREMENT PRIMARY KEY,
        patient_id INT NOT NULL,
        doctor_id INT NOT NULL,
        appointment_date DATE,
        appointment_time TIME,
        status VARCHAR(20) DEFAULT 'Booked',
        FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
        FOREIGN KEY (doctor_id) REFERENCES doctors(id) ON DELETE CASCADE
    ) ENGINE=InnoDB;
    """
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(ddl_patients)
        cur.execute(ddl_doctors)
        cur.execute(ddl_appointments)
        conn.commit()
        cur.close()
    except Exception as e:
        print(f"[DB Init Error] {e}")
    finally:
        if conn:
            conn.close()

def sql_date_from_ddmmyyyy(s):
    """Convert dd-mm-yyyy to yyyy-mm-dd (for DATE column)."""
    try:
        return datetime.strptime(s, "%d-%m-%Y").strftime("%Y-%m-%d")
    except Exception:
        return None

def sql_time_from_HHMM(s):
    """Validate HH:MM and return same string (MySQL TIME accepts 'HH:MM:SS', but 'HH:MM' works)."""
    try:
        dt = datetime.strptime(s, "%H:%M")
        return dt.strftime("%H:%M:%S")
    except Exception:
        return None
    
def auto_fix_old_doctors():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE doctors
        SET username = CAST(id AS CHAR),
            password = CONCAT('doctor_', CAST(id AS CHAR))
        WHERE username IS NULL OR password IS NULL 
              OR username = '' OR password = '';
    """)

    conn.commit()
    cur.close()
    conn.close()

    
#-------------otp-------
def generate_otp():
    """Generate 4-digit OTP."""
    return str(random.randint(1000, 9999))


# ---------------- Input validation helpers ----------------
def validate_date(date_str):
    try:
        datetime.strptime(date_str, "%d-%m-%Y")
        return True
    except ValueError:
        return False

def validate_integer(prompt):
    while True:
        try:
            val = input(prompt).strip()
            if not val:
                print("Input cannot be empty.")
                continue
            return int(val)
        except ValueError:
            print("Please enter a valid integer.")

def validate_date_input(prompt):
    while True:
        date_str = input(prompt).strip()
        if not date_str:
            print("Input cannot be empty.")
            continue
        if validate_date(date_str):
            return date_str
        print("Invalid date format. Use dd-mm-yyyy (e.g., 15-10-2023).")

def validate_time_input(prompt):
    while True:
        time_str = input(prompt).strip()
        if not time_str:
            print("Input cannot be empty.")
            continue
        try:
            datetime.strptime(time_str, "%H:%M")
            return time_str
        except ValueError:
            print("Invalid time format. Use HH:MM (24-hour).")

def validate_phone(prompt):
    while True:
        phone = input(prompt).strip()
        if not phone:
            print("Input cannot be empty.")
            continue
        if len(phone) == 10 and phone.isdigit():
            return phone
        print("Please enter a valid 10-digit mobile number (numbers only).")

# ---------------- Authentication ----------------
def authenticate():
    username = "admin"
    password = "pass123"
    attempts = 0

    while attempts < 3:
        u = input("Enter username: ").strip()
        p = input("Enter password: ").strip()
        if u.lower() == username and p == password:
            print("Login successful.")
            return True
        else:
            print("Login failed. Try again.")
            attempts += 1
    print("Too many failed attempts. Access denied.")
    return False

# ---------------- Patient Management (DB) ----------------
def add_patient():
    name = input("Enter patient name: ").strip()
    age = validate_integer("Enter age: ")
    gender = input("Enter gender: ").strip().title()
    dob = validate_date_input("Enter DOB (dd-mm-yyyy): ")
    contact = validate_phone("Enter contact: ")
    symptoms = input("Enter symptoms: ").strip()

    conn = get_db_connection()
    cur = conn.cursor()

    otp = generate_otp()
    cur.execute("""INSERT INTO patients (name, age, gender, dob, contact, symptoms, otp_code)
                   VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                (name, age, gender, sql_date_from_ddmmyyyy(dob), contact, symptoms, otp))
    conn.commit()
    pid = cur.lastrowid
    print(f"✅ Patient registered (ID: {pid}). OTP assigned: {otp}")
    cur.close()
    conn.close()

def verify_patient_otp(pid):
    """Check if entered OTP matches."""
    otp_input = input("Enter your 4-digit OTP: ").strip()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT otp_code FROM patients WHERE id=%s", (pid,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row and otp_input == row[0]:
        return True
    print("❌ Invalid OTP.")
    return False

def view_patients(term=None, search_id=None, show_otp=True):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)

        if term:
            like = f"%{term}%"
            try:
                search_id = int(term)
            except ValueError:
                search_id = None

            if search_id is not None:
                cur.execute("""
                    SELECT * FROM patients 
                    WHERE id = %s OR name LIKE %s OR contact LIKE %s 
                    ORDER BY id
                """, (search_id, like, like))
            else:
                cur.execute("""
                    SELECT * FROM patients 
                    WHERE name LIKE %s OR contact LIKE %s 
                    ORDER BY id
                """, (like, like))
        else:
            cur.execute("SELECT * FROM patients ORDER BY id")

        rows = cur.fetchall()

        if not rows:
            print("No patient records found.")
            return

        print("\n--- Patient Details ---")
        for r in rows:
            dob = r['dob'].strftime("%d-%m-%Y") if hasattr(r['dob'], "strftime") else (r['dob'] or "")
            base_info = f"ID: {r['id']} | Name: {r['name']} | Age: {r['age']} | Gender: {r['gender']} | DOB: {dob} | Contact: {r['contact']} | Symptoms: {r['symptoms']}"
            if show_otp:
                base_info += f" | OTP: {r.get('otp_code', 'N/A')}"
            print(base_info)

        cur.close()

    except Exception as e:
        print(f"[DB Error] Could not read patients: {e}")

    finally:
        if conn:
            conn.close()


def search_patients(role="admin"):
    """
    Search patients by name, contact, or ID.
    OTP visibility is controlled based on role.
    """
    term = input("Enter patient name, contact, or ID to search: ").strip()
    if not term:
        print("No search term provided.")
        return

    # Determine if OTP should be shown
    show_otp = role.lower() != "doctor"

    # Try to convert term to integer for ID search
    try:
        search_id = int(term)
    except ValueError:
        search_id = None

    # Call view_patients with OTP visibility flag
    view_patients(term=term, search_id=search_id, show_otp=show_otp)



def edit_patient():
    pid = validate_integer("Enter patient ID to edit: ")
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM patients WHERE id = %s", (pid,))
        r = cur.fetchone()
        if not r:
            print(f"Patient ID {pid} not found.")
            return
        print(f"\nCurrent: ID: {r['id']} | Name: {r['name']} | Age: {r['age']} | Gender: {r['gender']} | DOB: {r['dob']} | Contact: {r['contact']} | Symptoms: {r['symptoms']}")
        name = input(f"Enter new name (leave blank to keep '{r['name']}'): ").strip() or r['name']
        age_input = input(f"Enter new age (leave blank to keep '{r['age']}'): ").strip()
        age = int(age_input) if age_input else r['age']
        gender = input(f"Enter new gender (leave blank to keep '{r['gender']}'): ").strip().title() or r['gender']
        dob_input = input(f"Enter new DOB (dd-mm-yyyy) (leave blank to keep '{r['dob']}'): ").strip()
        dob_sql = sql_date_from_ddmmyyyy(dob_input) if dob_input else (r['dob'].strftime("%Y-%m-%d") if r['dob'] else None)
        contact = input(f"Enter new contact (leave blank to keep '{r['contact']}'): ").strip() or r['contact']
        symptoms = input(f"Enter new symptoms (leave blank to keep current): ").strip() or r['symptoms']

        cur.execute("""UPDATE patients SET name=%s, age=%s, gender=%s, dob=%s, contact=%s, symptoms=%s WHERE id=%s""",
                    (name, age, gender, dob_sql, contact, symptoms, pid))
        conn.commit()
        print(f"✅ Patient ID {pid} updated successfully.")
        cur.close()
    except mysql.connector.IntegrityError as ie:
        print("Update failed: contact must be unique or constraint violation.")
    except Exception as e:
        print(f"[DB Error] Could not edit patient: {e}")
    finally:
        if conn:
            conn.close()

# ---------------- Doctor Management with Authentication ----------------

def add_doctor():
    name = input("Enter doctor name: ").strip()
    if not name:
        print("Name cannot be empty.")
        return

    spec = input("Enter specialization: ").strip()
    if not spec:
        print("Specialization cannot be empty.")
        return

    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Insert doctor first (ID auto-generated)
        cur.execute(
            "INSERT INTO doctors (name, specialization) VALUES (%s, %s)",
            (name, spec)
        )

        doctor_id = cur.lastrowid  # Newly created ID

        # Auto-generate username and password
        username = str(doctor_id)
        password = f"doctor_{doctor_id}"   # As you wanted

        # Update doctor row with login credentials
        cur.execute(
            "UPDATE doctors SET username=%s, password=%s WHERE id=%s",
            (username, password, doctor_id)
        )

        conn.commit()

        print(f"\nDoctor added successfully with ID: {doctor_id}")
        print(f"Login credentials generated.")

        cur.close()

    except Exception as e:
        print(f"[DB Error] Could not add doctor: {e}")

    finally:
        if conn:
            conn.close()




def doctor_authenticate():
    print("\n--- Doctor Login ---")

    attempts = 0
    while attempts < 3:
        username = input("Enter your username (Doctor ID): ").strip()
        password = input("Enter your password: ").strip()

        conn = get_db_connection()
        cur = conn.cursor()

        # Check username + password
        cur.execute(
            "SELECT id FROM doctors WHERE username=%s AND password=%s",
            (username, password)
        )
        row = cur.fetchone()

        cur.close()
        conn.close()

        if row:
            doctor_id = row[0]
            print(f"\nLogin successful. Welcome Doctor ID: {doctor_id}")
            return doctor_id  # return logged-in doctor's ID

        else:
            print("❌ Incorrect username or password. Try again.")
            attempts += 1

    print("\n❌ Too many failed attempts. Access denied.")
    return None



def view_appointments_for_doctor(did):
    """Show only appointments for logged-in doctor."""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("""SELECT a.id, a.patient_id, a.appointment_date, a.appointment_time, a.status
                       FROM appointments a
                       WHERE a.doctor_id=%s AND a.status!='Cancelled'
                       ORDER BY a.appointment_date, a.appointment_time""", (did,))
        rows = cur.fetchall()
        if not rows:
            print("No appointments found.")
            return

        print("\n--- Your Appointments ---")
        for r in rows:
            date_str = r['appointment_date'].strftime("%d-%m-%Y") if r['appointment_date'] else ""
            if r['appointment_time']:
                if hasattr(r['appointment_time'], 'seconds'):
                    total_seconds = r['appointment_time'].seconds
                    hours = total_seconds // 3600
                    minutes = (total_seconds % 3600) // 60
                    time_str = f"{hours:02d}:{minutes:02d}"
                else:
                    time_str = r['appointment_time'].strftime("%H:%M")
            else:
                time_str = ""
            print(f"ID: {r['id']} | Patient ID: {r['patient_id']} | Date: {date_str} | Time: {time_str} | Status: {r['status']}")
        cur.close()
    except Exception as e:
        print(f"[DB Error] Could not read appointments: {e}")
    finally:
        if conn:
            conn.close()


def view_doctors(search_term=None):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)

        if search_term:
            like = f"%{search_term}%"
            cur.execute("""SELECT * FROM doctors 
                           WHERE name LIKE %s OR specialization LIKE %s 
                           ORDER BY id""", (like, like))
        else:
            cur.execute("SELECT * FROM doctors ORDER BY id")

        rows = cur.fetchall()
        if not rows:
            print("No doctor records found.")
            return

        print("\n--- Doctor Details ---")
        for r in rows:
            print(f"ID: {r['id']} | Name: {r['name']} | Specialization: {r['specialization']}")
        cur.close()
    except Exception as e:
        print(f"[DB Error] Could not read doctors: {e}")
    finally:
        if conn:
            conn.close()



def search_doctors():
    term = input("Enter doctor name or specialization to search: ").strip()
    if not term:
        print("No search term provided.")
        return
    view_doctors(term)



def edit_doctor():
    did = validate_integer("Enter doctor ID to edit: ")
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM doctors WHERE id = %s", (did,))
        r = cur.fetchone()
        if not r:
            print(f"Doctor ID {did} not found.")
            return
        print(f"Current: ID: {r['id']} | Name: {r['name']} | Specialization: {r['specialization']}")
        name = input(f"Enter new name (leave blank to keep '{r['name']}'): ").strip() or r['name']
        spec = input(f"Enter new specialization (leave blank to keep '{r['specialization']}'): ").strip() or r['specialization']
        cur.execute("UPDATE doctors SET name=%s, specialization=%s WHERE id=%s", (name, spec, did))
        conn.commit()
        print(f"✅ Doctor ID {did} updated successfully.")
        cur.close()
    except Exception as e:
        print(f"[DB Error] Could not edit doctor: {e}")
    finally:
        if conn:
            conn.close()

# ---------------- Appointment Management (DB) ----------------
def patient_exists(pid):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM patients WHERE id=%s", (pid,))
        res = cur.fetchone()
        cur.close()
        return bool(res)
    except Exception:
        return False
    finally:
        if conn:
            conn.close()

def doctor_exists(did):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM doctors WHERE id=%s", (did,))
        res = cur.fetchone()
        cur.close()
        return bool(res)
    except Exception:
        return False
    finally:
        if conn:
            conn.close()

def has_conflict(did, date_sql, time_sql):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""SELECT 1 FROM appointments 
                       WHERE doctor_id=%s AND appointment_date=%s AND appointment_time=%s AND status!='Cancelled'""",
                    (did, date_sql, time_sql))
        res = cur.fetchone()
        cur.close()
        return bool(res)
    except Exception:
        return False
    finally:
        if conn:
            conn.close()

def book_appointment(is_admin=False):
    pid = validate_integer("Enter patient ID: ")
    did = validate_integer("Enter doctor ID: ")

    if not patient_exists(pid):
        print("❌ Patient not found.")
        return
    if not doctor_exists(did):
        print("❌ Doctor not found.")
        return
    if not is_admin and not verify_patient_otp(pid):
        return

    date = validate_date_input("Enter date (dd-mm-yyyy): ")
    time = validate_time_input("Enter time (HH:MM): ")
    date_sql, time_sql = sql_date_from_ddmmyyyy(date), sql_time_from_HHMM(time)

    if has_conflict(did, date_sql, time_sql):
        print("⚠️ Doctor already booked at that time.")
        return

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""INSERT INTO appointments (patient_id, doctor_id, appointment_date, appointment_time)
                   VALUES (%s,%s,%s,%s)""", (pid, did, date_sql, time_sql))
    conn.commit()
    print(f"✅ Appointment booked (ID: {cur.lastrowid})")
    cur.close()
    conn.close()


def view_appointments(search_term=None, doctor_id=None):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)

        query = """SELECT a.id, a.patient_id, a.doctor_id, a.appointment_date, a.appointment_time, a.status
                   FROM appointments a
                   WHERE a.status != 'Cancelled'"""
        params = []

        # Filter by doctor if doctor_id provided
        if doctor_id:
            query += " AND doctor_id=%s"
            params.append(doctor_id)

        # Filter by search_term if provided
        if search_term:
            like = f"%{search_term}%"
            query += """ AND (
                        CAST(a.id AS CHAR) LIKE %s OR
                        CAST(a.patient_id AS CHAR) LIKE %s OR
                        CAST(a.appointment_date AS CHAR) LIKE %s OR
                        CAST(a.appointment_time AS CHAR) LIKE %s
                       )"""
            params.extend([like, like, like, like])

        query += " ORDER BY a.appointment_date, a.appointment_time"

        cur.execute(query, tuple(params))
        rows = cur.fetchall()

        if not rows:
            print("No appointments found.")
            return

        print("\n--- Appointments ---")
        for r in rows:
            date_str = r['appointment_date'].strftime("%d-%m-%Y") if r['appointment_date'] else ""
            if r['appointment_time']:
                if hasattr(r['appointment_time'], 'seconds'):
                    total_seconds = r['appointment_time'].seconds
                    hours = total_seconds // 3600
                    minutes = (total_seconds % 3600) // 60
                    time_str = f"{hours:02d}:{minutes:02d}"
                else:
                    time_str = r['appointment_time'].strftime("%H:%M")
            else:
                time_str = ""
            print(f"ID: {r['id']} | Patient ID: {r['patient_id']} | Doctor ID: {r['doctor_id']} | Date: {date_str} | Time: {time_str} | Status: {r['status']}")
        cur.close()
    except Exception as e:
        print(f"[DB Error] Could not read appointments: {e}")
    finally:
        if conn:
            conn.close()


def search_appointments():
    term = input("Enter ID, patient ID, doctor ID, date (dd-mm-yyyy) or time (HH:MM) to search: ").strip()
    if not term:
        print("No search term provided.")
        return
    # if user enters date in dd-mm-yyyy, convert for search convenience
    if validate_date(term):
        term = datetime.strptime(term, "%d-%m-%Y").strftime("%Y-%m-%d")
    view_appointments(term)

def cancel_appointment(is_admin=False):
    aid = validate_integer("Enter appointment ID: ")
    pid = validate_integer("Enter your patient ID: ") if not is_admin else None

    if not is_admin and not verify_patient_otp(pid):
        return

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE appointments SET status='Cancelled' WHERE id=%s", (aid,))
    if cur.rowcount:
        conn.commit()
        print("✅ Appointment cancelled.")
    else:
        print("❌ Appointment not found.")
    cur.close()
    conn.close()
            
def view_cancelled_appointments():
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("""SELECT * FROM appointments WHERE status='Cancelled' ORDER BY appointment_date, appointment_time""")
        rows = cur.fetchall()
        if not rows:
            print("No cancelled appointments found.")
            return
        print("\n--- Cancelled Appointments ---")
        for r in rows:
            date_str = r['appointment_date'] if r['appointment_date'] else ""
            time_str = str(r['appointment_time'])
            print(f"ID: {r['id']} | Patient ID: {r['patient_id']} | Doctor ID: {r['doctor_id']} | Date: {date_str} | Time: {time_str} | Status: {r['status']}")
        cur.close()
    except Exception as e:
        print(f"[DB Error] Could not read cancelled appointments: {e}")
    finally:
        if conn:
            conn.close()


# ---------------- Role-Based Menus ----------------

def patient_menu():
    while True:
        print("\n===== PATIENT MENU =====")
        print("1. Register New Patient")
        print("2. View All Doctors")
        print("3. Search Doctor")
        print("4. Book Appointment")
        print("5. Cancel Appointment")
        print("6. Exit to Main Menu")

        choice = input("Enter your choice: ").strip()
        if choice == "1":
            add_patient()
        elif choice == "2":
            view_doctors()
        elif choice == "3":
            search_doctors()
        elif choice == "4":
            book_appointment()
        elif choice == "5":
            cancel_appointment()
        elif choice == "6":
            print("Returning to main menu...")
            break
        else:
            print("Invalid choice. Try again.")


def doctor_menu():
    doctor_id = doctor_authenticate()
    if not doctor_id:
        return  # exit if authentication failed

    while True:
        print("\n===== DOCTOR MENU =====")
        print("1. View All Patients")
        print("2. Search Patient")
        print("3. View My Appointments") 
        print("4. Exit to Main Menu")

        choice = input("Enter your choice: ").strip()
        if choice == "1":
            view_patients(show_otp=False)
        elif choice == "2":
            search_patients(role="doctor")
        elif choice == "3":
            view_appointments(doctor_id=doctor_id)  # only show this doctor's appointments
        elif choice == "4":
            print("Returning to main menu...")
            break
        else:
            print("Invalid choice. Try again.")




def admin_menu():
    while True:
        print("\n===== ADMIN MENU =====")
        print("1. Register New Patient")
        print("2. View All Patients")
        print("3. Search Patients")
        print("4. Edit Patient Details")
        print("5. Add Doctor")
        print("6. View All Doctors")
        print("7. Search Doctors")
        print("8. Edit Doctor Details")
        print("9. Book Appointment")
        print("10. View Appointments")
        print("11. Cancel Appointment")
        print("12. View Cancelled Appointments")
        print("13. Exit to Main Menu")

        choice = input("Enter your choice: ").strip()
        if choice == "1":
            add_patient()
        elif choice == "2":
            view_patients()
        elif choice == "3":
            search_patients(role="admin")
        elif choice == "4":
            edit_patient()
        elif choice == "5":
            add_doctor()
        elif choice == "6":
            view_doctors()
        elif choice == "7":
            search_doctors()
        elif choice == "8":
            edit_doctor()
        elif choice == "9":
            book_appointment()
        elif choice == "10":
            view_appointments()
        elif choice == "11":
            cancel_appointment()
        elif choice == "12":
            view_cancelled_appointments()
        elif choice == "13":
            print("Returning to main menu...")
            break
        else:
            print("Invalid choice. Try again.")


# ---------------- Main Role Selection ----------------
def main_menu():
    while True:
        print("\n===== HOSPITAL MANAGEMENT SYSTEM =====")
        print("1. Patient")
        print("2. Doctor")
        print("3. Admin")
        print("4. Exit")

        role_choice = input("Select your role: ").strip()
        if role_choice == "1":
            patient_menu()
        elif role_choice == "2":
            doctor_menu()
        elif role_choice == "3":
            if authenticate():
                admin_menu()
            else:
                print("Returning to main menu...")
        elif role_choice == "4":
            print("Exiting system. Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")


# ---------------- Main ----------------
if __name__ == "__main__":
    auto_fix_old_doctors()  # ← ADD THIS LINE
    main_menu()             # your existing start function
