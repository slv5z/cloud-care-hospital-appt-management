import os
import csv
from pathlib import Path
from datetime import datetime

# File paths
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)  # Ensure data directory exists
PATIENTS_FILE = DATA_DIR / "patients.txt"
DOCTORS_FILE = DATA_DIR / "doctors.txt"
APPOINTMENTS_FILE = DATA_DIR / "appointments.txt"

# ---------------- Helper Functions ----------------
def get_next_id(filename):
    """Get next ID by scanning the file for the last ID."""
    if not filename.exists():
        return 1
    last_id = 0
    try:
        with open(filename, "r", newline="") as f:
            reader = csv.reader(f)
            for row in reader:
                if row and row[0].strip():
                    try:
                        id_val = int(row[0])
                        last_id = max(last_id, id_val)
                    except ValueError:
                        continue  # Skip invalid rows
    except IOError as e:
        print(f"Error reading {filename}: {e}")
        return 1
    return last_id + 1

def file_exists(filename):
    return filename.exists() and filename.stat().st_size > 0

def validate_date(date_str):
    """Basic date validation (dd-mm-yyyy)."""
    try:
        datetime.strptime(date_str, "%d-%m-%Y")
        return True
    except ValueError:
        return False

def validate_integer(prompt):
    """Get validated integer input."""
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
    """Get validated date input."""
    while True:
        date_str = input(prompt).strip()
        if not date_str:
            print("Input cannot be empty.")
            continue
        if validate_date(date_str):
            return date_str
        print("Invalid date format. Use dd-mm-yyyy (e.g., 15-10-2023).")

def validate_time_input(prompt):
    """Get validated time input (HH:MM, 24-hour format)."""
    while True:
        time_str = input(prompt).strip()
        if not time_str:
            print("Input cannot be empty.")
            continue
        try:
            datetime.strptime(time_str, "%H:%M")
            return time_str
        except ValueError:
            print("Invalid time format. Use HH:MM (e.g., 14:30, 09:00).")

def validate_phone(prompt):
    """Get validated 10-digit phone number input."""
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

# ---------------- Patient Management ----------------
def add_patient():
    pid = get_next_id(PATIENTS_FILE)
    name = input("Enter patient name: ").strip()
    if not name:
        print("Name cannot be empty.")
        return
    age = validate_integer("Enter patient age: ")
    gender = input("Enter patient gender: ").strip().title()
    dob = validate_date_input("Enter patient date of birth (dd-mm-yyyy): ")
    contact = validate_phone("Enter patient contact number: ")
    symptoms = input("Enter patient symptoms/problem: ").strip()

    if contact_exists(contact):
        print("Patient with this contact already exists.")
        return

    try:
        with open(PATIENTS_FILE, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([pid, name, age, gender, dob, contact, symptoms])
        print(f"Patient registered successfully with ID: {pid}")
    except IOError as e:
        print(f"Error saving patient: {e}")

def contact_exists(contact):
    if not file_exists(PATIENTS_FILE):
        return False
    try:
        with open(PATIENTS_FILE, "r", newline="") as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 6 and row[5].strip() == contact:
                    return True
    except IOError:
        pass
    return False

def view_patients(search_term=None):
    if not file_exists(PATIENTS_FILE):
        print("No patient records found.")
        return
    try:
        with open(PATIENTS_FILE, "r", newline="") as f:
            reader = csv.reader(f)
            rows = list(reader)
            if not rows:
                print("No data available in patients file.")
                return
            print("\n--- Patient Details ---")
            for row in rows:
                if len(row) < 7:
                    continue
                pid, name, age, gender, dob, contact, symptoms = row
                if search_term:
                    if search_term.lower() in name.lower() or search_term.lower() in contact.lower():
                        print(f"ID: {pid} | Name: {name} | Age: {age} | Gender: {gender} | DOB: {dob} | Contact: {contact} | Symptoms: {symptoms}")
                else:
                    print(f"ID: {pid} | Name: {name} | Age: {age} | Gender: {gender} | DOB: {dob} | Contact: {contact} | Symptoms: {symptoms}")
            if search_term:
                print(f"Search completed for '{search_term}'.")
    except IOError as e:
        print(f"Error reading patients: {e}")

def search_patients():
    search_term = input("Enter name or contact to search: ").strip()
    if not search_term:
        print("No search term provided.")
        return
    view_patients(search_term)

# ---------------- Doctor Management ----------------
def add_doctor():
    did = get_next_id(DOCTORS_FILE)
    name = input("Enter doctor name: ").strip()
    if not name:
        print("Name cannot be empty.")
        return
    spec = input("Enter specialization: ").strip()
    if not spec:
        print("Specialization cannot be empty.")
        return
    try:
        with open(DOCTORS_FILE, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([did, name, spec])
        print(f"Doctor added successfully with ID: {did}")
    except IOError as e:
        print(f"Error saving doctor: {e}")

def view_doctors(search_term=None):
    if not file_exists(DOCTORS_FILE):
        print("No doctor records found.")
        return
    try:
        with open(DOCTORS_FILE, "r", newline="") as f:
            reader = csv.reader(f)
            rows = list(reader)
            if not rows:
                print("No data available in doctors file.")
                return
            print("\n--- Doctor Details ---")
            for row in rows:
                if len(row) < 3:
                    continue
                did, name, spec = row
                if search_term:
                    if search_term.lower() in name.lower():
                        print(f"ID: {did} | Name: {name} | Specialization: {spec}")
                else:
                    print(f"ID: {did} | Name: {name} | Specialization: {spec}")
            if search_term:
                print(f"Search completed for '{search_term}'.")
    except IOError as e:
        print(f"Error reading doctors: {e}")

def search_doctors():
    search_term = input("Enter name to search: ").strip()
    if not search_term:
        print("No search term provided.")
        return
    view_doctors(search_term)

# ---------------- Appointment Management ----------------
def patient_exists(pid):
    if not file_exists(PATIENTS_FILE):
        return False
    with open(PATIENTS_FILE, "r", newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) >= 1 and row[0].strip() == str(pid):
                return True
    return False

def doctor_exists(did):
    if not file_exists(DOCTORS_FILE):
        return False
    with open(DOCTORS_FILE, "r", newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) >= 1 and row[0].strip() == str(did):
                return True
    return False

def has_conflict(did, date, time_slot):
    if not file_exists(APPOINTMENTS_FILE):
        return False
    with open(APPOINTMENTS_FILE, "r", newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) < 5:
                continue
            _, _, row_did, row_date, row_time = row
            if row_did.strip() == str(did) and row_date.strip() == date and row_time.strip() == time_slot:
                return True
    return False

def book_appointment():
    aid = get_next_id(APPOINTMENTS_FILE)
    pid = validate_integer("Enter patient ID: ")
    did = validate_integer("Enter doctor ID: ")

    if not patient_exists(pid):
        print("Patient ID not found.")
        return
    if not doctor_exists(did):
        print("Doctor ID not found.")
        return

    date = validate_date_input("Enter date (dd-mm-yyyy): ")
    time_slot = validate_time_input("Enter time (HH:MM): ")

    while has_conflict(did, date, time_slot):
        print("Conflict: Doctor already has an appointment at this time on this date.")
        time_slot = validate_time_input("Please enter a different time (HH:MM): ")

    try:
        with open(APPOINTMENTS_FILE, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([aid, pid, did, date, time_slot])
        print(f"Appointment booked successfully with ID: {aid}")
    except IOError as e:
        print(f"Error booking appointment: {e}")

def view_appointments(search_term=None):
    if not file_exists(APPOINTMENTS_FILE):
        print("No appointments found.")
        return
    try:
        with open(APPOINTMENTS_FILE, "r", newline="") as f:
            reader = csv.reader(f)
            rows = list(reader)
            print("\n--- Appointments ---")
            for row in rows:
                if len(row) < 5:
                    continue
                aid, pid, did, date, time_slot = row
                if search_term and search_term not in f"{aid} {pid} {did} {date} {time_slot}":
                    continue
                print(f"ID: {aid} | Patient ID: {pid} | Doctor ID: {did} | Date: {date} | Time: {time_slot}")
    except IOError as e:
        print(f"Error reading appointments: {e}")

def cancel_appointment():
    if not file_exists(APPOINTMENTS_FILE):
        print("No appointments to cancel.")
        return
    aid = validate_integer("Enter appointment ID to cancel: ")
    found = False
    lines = []
    try:
        with open(APPOINTMENTS_FILE, "r", newline="") as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 1 and row[0].strip() != str(aid):
                    lines.append(row)
                else:
                    found = True
        if found:
            with open(APPOINTMENTS_FILE, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerows(lines)
            print(f"Appointment ID {aid} canceled successfully.")
        else:
            print(f"Appointment ID {aid} not found.")
    except IOError as e:
        print(f"Error canceling appointment: {e}")

 # ---------------- edit details ----------------
def edit_patient():
    pid = validate_integer("Enter patient ID to edit: ")
    lines = []
    updated = False
    try:
        with open(PATIENTS_FILE, "r", newline="") as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 7 and row[0].strip() == str(pid):
                    print(f"\nCurrent Details:\nID: {row[0]} | Name: {row[1]} | Age: {row[2]} | Gender: {row[3]} | DOB: {row[4]} | Contact: {row[5]} | Symptoms: {row[6]}")
                    name = input(f"Enter new name (leave blank to keep '{row[1]}'): ").strip()
                    age_input = input(f"Enter new age (leave blank to keep '{row[2]}'): ").strip()
                    gender = input(f"Enter new gender (leave blank to keep '{row[3]}'): ").strip().title()
                    dob = input(f"Enter new DOB (leave blank to keep '{row[4]}'): ").strip()
                    contact = input(f"Enter new contact (leave blank to keep '{row[5]}'): ").strip()
                    symptoms = input(f"Enter new symptoms (leave blank to keep '{row[6]}'): ").strip()

                    new_row = [
                        row[0],
                        name if name else row[1],
                        age_input if age_input else row[2],
                        gender if gender else row[3],
                        dob if dob else row[4],
                        contact if contact else row[5],
                        symptoms if symptoms else row[6]
                    ]
                    lines.append(new_row)
                    updated = True
                else:
                    lines.append(row)

        if updated:
            with open(PATIENTS_FILE, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerows(lines)
            print(f"✅ Patient ID {pid} updated successfully.")
        else:
            print(f"❌ Patient ID {pid} not found.")
    except IOError as e:
        print(f"Error editing patient: {e}")


def edit_doctor():
    did = validate_integer("Enter doctor ID to edit: ")
    lines = []
    updated = False
    try:
        with open(DOCTORS_FILE, "r", newline="") as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 3 and row[0].strip() == str(did):
                    print(f"\nCurrent Details:\nID: {row[0]} | Name: {row[1]} | Specialization: {row[2]}")
                    name = input(f"Enter new name (leave blank to keep '{row[1]}'): ").strip()
                    spec = input(f"Enter new specialization (leave blank to keep '{row[2]}'): ").strip()

                    new_row = [row[0], name if name else row[1], spec if spec else row[2]]
                    lines.append(new_row)
                    updated = True
                else:
                    lines.append(row)

        if updated:
            with open(DOCTORS_FILE, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerows(lines)
            print(f"✅ Doctor ID {did} updated successfully.")
        else:
            print(f"❌ Doctor ID {did} not found.")
    except IOError as e:
        print(f"Error editing doctor: {e}")

        

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
    while True:
        print("\n===== DOCTOR MENU =====")
        print("1. View All Patients")
        print("2. Search Patient")
        print("3. View Appointments")
        print("4. Exit to Main Menu")

        choice = input("Enter your choice: ").strip()
        if choice == "1":
            view_patients()
        elif choice == "2":
            search_patients()
        elif choice == "3":
            view_appointments()
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
        print("12. Exit to Main Menu")

        choice = input("Enter your choice: ").strip()
        if choice == "1":
            add_patient()
        elif choice == "2":
            view_patients()
        elif choice == "3":
            search_patients()
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
    main_menu()