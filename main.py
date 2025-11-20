import uvicorn
from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import RedirectResponse ,  HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import crud, models
from db import get_db
from models import Appointment , Doctor , Patient
from db import SessionLocal, engine
from fastapi.staticfiles import StaticFiles
import random
from starlette.middleware.sessions import SessionMiddleware
# ---------------- Setup ----------------
models.Base.metadata.create_all(bind=engine)
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
app.add_middleware(SessionMiddleware, secret_key="your-secret-key")

# ---------------- Role Dashboard ----------------
@app.get("/")
def role_dashboard(request: Request):
    return templates.TemplateResponse("role_dashboard.html", {"request": request})
@app.post("/select_role")
def select_role(request: Request, role: str = Form(...)):
    """Include request param if you later want to pass messages in templates"""
    if role == "patient":
        return RedirectResponse("/patient", status_code=303)
    elif role == "doctor":
        return RedirectResponse("/doctor/login", status_code=303)
    elif role == "admin":
        return RedirectResponse("/admin/login", status_code=303)
    else:
        raise HTTPException(status_code=400, detail="Invalid role")
# ---------------- Patient Dashboard ----------------
@app.get("/patient", name="patient_dashboard")
def patient_dashboard(request: Request):
    return templates.TemplateResponse("patient_dashboard.html", {"request": request})
# ---------- REGISTER PATIENT (OTP GENERATED) ----------
@app.get("/patient/add")
def add_patient_page(request: Request):
    return templates.TemplateResponse("add_patient.html", {"request": request})
@app.post("/patient/add")
def add_patient_form(
    request: Request,
    name: str = Form(...),
    age: int = Form(...),
    gender: str = Form(...),
    dob: str = Form(...),
    contact: str = Form(...),
    symptoms: str = Form(""),
    db: Session = Depends(get_db)
    ):
    patient = crud.create_patient(db, name, age, gender, dob, contact, symptoms)
    return templates.TemplateResponse(
    "add_patient.html",
    {
    "request": request,
    "message": "Patient registered successfully!",
    "otp": patient.otp_code,   # ✅ Pass OTP here
    "patient_id": patient.id,
    "source": "patient"
    }
    )
# ---------- PATIENT DASHBOARD ACTIONS ----------
@app.post("/patient_action")
def patient_action(action: str = Form(...)):
    actions_map = {
    "add_patient": "/patient/add",
    "view_doctors": "/patient/view_doctors",
    "search_doctors": "/patient/search_doctors",
    "book_appointment": "/patient/book_appointment",
    "view_appointments_auth": "/patient/view_appointments_auth",
    "cancel_appointment": "/patient/cancel_appointment",
    "exit": "/"
    }
    if action in actions_map:
        return RedirectResponse(actions_map[action], status_code=303)
    raise HTTPException(status_code=400, detail="Invalid action")
# ---------- VIEW & SEARCH DOCTORS ----------
@app.get("/patient/view_doctors")
def view_doctors(request: Request, db: Session = Depends(get_db)):
    doctors = crud.get_doctors(db)
    return templates.TemplateResponse("view_doctors.html", {"request": request, "doctors": doctors})
@app.get("/patient/search_doctors")
@app.get("/patient/search_doctors/")
def handle_search_doctors(request: Request, term: str = "", db: Session = Depends(get_db)):
    doctors = crud.search_doctor(db, term) if term else []
    return templates.TemplateResponse(
    "search_doctors.html",
    {"request": request, "doctors": doctors, "searched": term}
    )
# ---------- BOOK APPOINTMENT (OTP REQUIRED for Patient only) ----------
@app.get("/patient/book_appointment")
def patient_book_appointment_page(request: Request, db: Session = Depends(get_db)):
    patients = crud.get_patients(db)
    doctors = crud.get_doctors(db)
    return templates.TemplateResponse(
    "book_appointment.html",
    {
    "request": request,
    "patients": crud.get_patients(db),
    "doctors": crud.get_doctors(db),
    "source": "patient"
    }
    )
@app.post("/patient/book_appointment")
def book_appointment_post(
    request: Request,
    db: Session = Depends(get_db),
    patient_id: int = Form(...),
    doctor_id: int = Form(...),
    appointment_date: str = Form(...),
    appointment_time: str = Form(...),
    otp: str = Form(...)
    ):
    # Convert to correct variable names
    date = appointment_date
    time = appointment_time
    otp_code = otp
    # 1️⃣ Verify Patient
    patient = crud.get_patient(db, patient_id)
    if not patient:
        return templates.TemplateResponse(
            "book_appointment.html",
            {
                "request": request,
                "patients": crud.get_patients(db),
                "doctors": crud.get_doctors(db),
                "source": "patient",
                "message": "❌ Invalid patient ID!"
            }
        )
    # 2️⃣ Verify OTP
    if patient.otp_code != otp_code:
        return templates.TemplateResponse(
            "book_appointment.html",
            {
                "request": request,
                "patients": crud.get_patients(db),
                "doctors": crud.get_doctors(db),
                "source": "patient",
                "message": "❌ Incorrect OTP. Try again."
            }
        )
    # 3️⃣ Create Appointment
    appointment = crud.create_appointment(
        db,
        patient_id=patient_id,
        doctor_id=doctor_id,
        date=date,
        time=time
    )
    # 4️⃣ Success message
    return templates.TemplateResponse(
        "book_appointment.html",
        {
            "request": request,
            "patients": crud.get_patients(db),
            "doctors": crud.get_doctors(db),
            "source": "patient",
            "success": f"Appointment booked! ID: {appointment.id}"
        }
    )
# ---------- VIEW & CANCEL APPOINTMENTS ----------
@app.get("/patient/view_appointments")
def view_patient_appointments(request: Request, db: Session = Depends(get_db)):
    appointments = crud.get_appointments(db)
    return templates.TemplateResponse("view_appointments.html", {"request": request, "appointments": appointments})
@app.get("/patient/view_appointments_auth")
def view_appointments_auth_page(request: Request):
    return templates.TemplateResponse("view_appointments_auth.html", {"request": request})
@app.post("/patient/view_appointments_auth")
def view_appointments_auth(
    request: Request,
    patient_id: int = Form(...),
    otp: str = Form(...),
    db: Session = Depends(get_db)
    ):
    # Verify patient exists
    patient = crud.get_patient(db, patient_id)
    if not patient:
        return templates.TemplateResponse(
        "view_appointments_auth.html",
        {"request": request, "message": "❌ Invalid patient ID!"}
        )
    # Verify OTP
    if patient.otp_code != otp:
        return templates.TemplateResponse(
        "view_appointments_auth.html",
        {"request": request, "message": "❌ Incorrect OTP. Try again."}
        )
    # Get appointments for this patient
    appointments = db.query(models.Appointment).filter(models.Appointment.patient_id == patient_id).all()
    return templates.TemplateResponse(
    "view_appointments.html",
    {"request": request, "appointments": appointments, "patient_name": patient.name}
    )
# ---------------- Cancel Appointment (Patient) ----------------
@app.get("/patient/cancel_appointment")
def patient_cancel_page(request: Request):
    return templates.TemplateResponse(
    "cancel_appointment.html",
    {
    "request": request,
    "form_action": "/patient/cancel_appointment",
    "back_link": "/patient",
    "source": "patient"
    }
    )
@app.post("/patient/cancel_appointment")
async def cancel_appointment(
    request: Request,
    appointment_id: int = Form(...),
    otp: str = Form(None),      # ⬅ OTP OPTIONAL
    db: Session = Depends(get_db)
):
    # Detect call source: patient or admin
    form_source = request.query_params.get("source", "patient")
    # OTP required ONLY for patient
    if form_source == "patient":
        if otp is None:
            return templates.TemplateResponse(
                "cancel_appointment.html",
                {
                    "request": request,
                    "form_action": "/patient/cancel_appointment?source=patient",
                    "back_link": "/patient",
                    "message": "OTP is required for patient cancellation!"
                }
            )
        # Validate OTP
        patient = db.query(models.Patient).filter(models.Patient.otp_code == otp).first()
        if not patient:
            return templates.TemplateResponse(
                "cancel_appointment.html",
                {
                    "request": request,
                    "form_action": "/patient/cancel_appointment?source=patient",
                    "back_link": "/patient",
                    "message": "Invalid OTP!"
                }
            )
    # Proceed with appointment cancellation
    appt = db.query(models.Appointment).filter(models.Appointment.id == appointment_id).first()
    if not appt:
        return templates.TemplateResponse(
            "cancel_appointment.html",
            {
                "request": request,
                "form_action": f"/patient/cancel_appointment?source={form_source}",
                "back_link": "/patient" if form_source=="patient" else "/admin",
                "message": "Appointment not found!"
            }
        )
    appt.status = "Cancelled"
    db.commit()
    return templates.TemplateResponse(
        "cancel_appointment.html",
        {
            "request": request,
            "success": "Appointment cancelled successfully!",
            "form_action": f"/patient/cancel_appointment?source={form_source}",
            "back_link": "/patient" if form_source=="patient" else "/admin"
        }
    )
# ---------------- Doctor Dashboard ----------------
@app.get("/doctor/dashboard")
def doctor_dashboard(request: Request, db: Session = Depends(get_db)):
    doctor_id = request.session.get("doctor_id")
    if not doctor_id:
        return RedirectResponse("/doctor/login", status_code=303)
    doctor = db.query(models.Doctor).filter(models.Doctor.id == doctor_id).first()
    return templates.TemplateResponse(
    "doctor_dashboard.html",
    {"request": request, "doctor": doctor}
    )
@app.post("/doctor/dashboard_action")
def doctor_dashboard_action(
    request: Request,
    action: str = Form(...)
    ):
    if "doctor_id" not in request.session:
        return RedirectResponse("/doctor/login", status_code=303)
    if action == "view_patients":
        return RedirectResponse("/doctor/view_patients", status_code=303)
    elif action == "search_patients":
        return RedirectResponse("/doctor/search_patients", status_code=303)
    elif action == "view_appointments":
        return RedirectResponse("/doctor/view_appointments", status_code=303)
    elif action == "logout":
        request.session.clear()
        return RedirectResponse("/doctor/login", status_code=303)
    else:
        raise HTTPException(status_code=400, detail="Invalid action")
@app.get("/doctor/view_patients")
def view_patients(request: Request, searchTerm: str = "", db: Session = Depends(get_db)):
# Call the updated get_patients with optional search term
    searchTerm = searchTerm.strip()
    patients = crud.get_patients(db, searchTerm)
    return templates.TemplateResponse(
    "search_patient.html",  # Render search + results in one page
    {"request": request, "patients": patients, "show_otp": False, "searchTerm": searchTerm}
    )
@app.get("/doctor/search_patients")
def search_patients(request: Request, searchTerm: str = "", db: Session = Depends(get_db)):
# Fetch patients based on ID, Name, or Contact
    patients = crud.get_patients(db, searchTerm) if searchTerm else None
    return templates.TemplateResponse(
    "search_patient.html",
    {
    "request": request,
    "patients": patients,
    "searchTerm": searchTerm,
    "show_otp": False
    }
    )
@app.get("/doctor/view_appointments")
def doctor_view_appointments(request: Request, db: Session = Depends(get_db)):
    doctor_id = request.session.get("doctor_id")
    if not doctor_id:
        return RedirectResponse("/doctor/login", status_code=303)
    appointments = crud.get_appointments_for_doctor(db, doctor_id)
    return templates.TemplateResponse(
    "view_appointments.html",
    {"request": request, "appointments": appointments}
    )
@app.get("/doctor/logout")
def doctor_logout(request: Request):
    request.session.clear()
    return RedirectResponse("/doctor/login", status_code=303)
# ---------------- Admin Dashboard ----------------
@app.get("/admin")
def admin_dashboard(request: Request):
    return templates.TemplateResponse("admin_dashboard.html", {"request": request})
@app.get("/admin/login")
def admin_login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})
@app.post("/admin/login")
def admin_login(username: str = Form(...), password: str = Form(...)):
    if username == "admin" and password == "pass123":
        return RedirectResponse("/admin", status_code=303)
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")
# ----------------------------
# ADMIN DASHBOARD ACTION HANDLER
# ----------------------------
@app.post("/admin_action")
def admin_action(action: str = Form(...)):
    routes = {
    "add_patient": "/admin/add_patient",
    "view_patients": "/admin/view_patients",
    "search_patients": "/admin/search_patients",
    "edit_patient": "/admin/edit_patient",
    "add_doctor": "/admin/add_doctor",
    "view_doctors": "/admin/view_doctors",
    "search_doctors": "/admin/search_doctors",
    "edit_doctor": "/admin/edit_doctor",
    "book_appointment": "/admin/book_appointment",
    "view_appointments": "/admin/view_appointments",
    "cancel_appointment": "/admin/cancel_appointment",
    "view_cancelled": "/admin/view_cancelled"
    }
    if action in routes:
        return RedirectResponse(routes[action], status_code=303)
    elif action == "exit":
        return RedirectResponse("/", status_code=303)
    else:
        raise HTTPException(status_code=400, detail="Invalid action")
# ----------------------------
# DOCTOR MANAGEMENT
# ----------------------------
@app.get("/admin/add_doctor")
def add_doctor_page(request: Request):
    return templates.TemplateResponse("add_doctor.html", {"request": request})
@app.post("/admin/add_doctor")
def add_doctor_form(
    name: str = Form(...),
    specialization: str = Form(...),
    db: Session = Depends(get_db)
    ):
    crud.create_doctor(db, name, specialization)
    return RedirectResponse("/admin", status_code=303)
# For GET
@app.get("/admin/search_doctors")
def search_doctor_page(request: Request):
    return templates.TemplateResponse("search_doctors.html", {"request": request})
# For POST
@app.post("/admin/search_doctors")
def search_doctor_form(request: Request, term: str = Form(...), db: Session = Depends(get_db)):
    doctors = crud.search_doctor(db, term)
    return templates.TemplateResponse(
    "search_doctors.html",
    {"request": request, "doctors": doctors, "searched": term}
    )
@app.get("/admin/view_doctors")
def view_doctors_page(request: Request, db: Session = Depends(get_db)):
    doctors = crud.get_doctors(db)  # fetch all doctors
    return templates.TemplateResponse(
    "view_doctors.html",
    {"request": request, "doctors": doctors}
    )
# ----------------------------  
# PATIENT MANAGEMENT - ADMIN  
# ----------------------------
@app.get("/admin/add_patient")
def add_patient_page(request: Request):
# Pass a flag to tell the template this is being opened from admin
    return templates.TemplateResponse("add_patient.html", {"request": request, "source": "admin"})
@app.post("/admin/add_patient")
def add_patient_form(
    request: Request,
    name: str = Form(...),
    age: int = Form(...),
    gender: str = Form(...),
    dob: str = Form(...),
    contact: str = Form(...),
    symptoms: str = Form(""),
    db: Session = Depends(get_db)
    ):
    crud.create_patient(db, name, age, gender, dob, contact, symptoms)
    return RedirectResponse("/admin/view_patients", status_code=303)  # redirect to view all patients
@app.get("/admin/view_patients")
def view_patients(request: Request, db: Session = Depends(get_db)):
    """
    View all patients. No search functionality here anymore.
    """
    patients = crud.get_patients(db)  # fetch all patients
    return templates.TemplateResponse(
    "view_patients.html",
    {
    "request": request,
    "patients": patients,
    "show_otp": True
    }
    )
@app.get("/admin/search_patients")
def search_patients_page(request: Request):
    return templates.TemplateResponse("search_patient.html", {"request": request, "show_otp": True})
@app.post("/admin/search_patients")
def search_patients_form(request: Request, term: str = Form(...), db: Session = Depends(get_db)):
    patients = crud.search_patient(db, term)
    return templates.TemplateResponse(
    "search_patient.html",
    {"request": request, "patients": patients, "searched": term, "show_otp": True}
    )
# ----------------------------
# APPOINTMENT MANAGEMENT
# ----------------------------
# ---------------- Admin Book Appointment ----------------
@app.get("/admin/book_appointment")
def admin_book_appointment_page(request: Request, db: Session = Depends(get_db)):
    patients = crud.get_patients(db)
    doctors = crud.get_doctors(db)
    return templates.TemplateResponse(
    "book_appointment.html",
    {"request": request, "patients": patients, "doctors": doctors, "source": "admin"}
    )
@app.post("/admin/book_appointment")
def admin_book_appointment(
    request: Request,
    patient_id: int = Form(...),
    doctor_id: int = Form(...),
    appointment_date: str = Form(...),
    appointment_time: str = Form(...),
    db: Session = Depends(get_db)
    ):
    appointment = crud.create_appointment(db, patient_id, doctor_id, appointment_date, appointment_time)
    message = f"Appointment booked successfully (Admin Access)! ID: {appointment.id}"
    patients = crud.get_patients(db)
    doctors = crud.get_doctors(db)
    return templates.TemplateResponse(
    "book_appointment.html",
    {"request": request, "message": message, "patients": patients, "doctors": doctors, "source": "admin"}
    )
# ----------------------------
# ADMIN: VIEW APPOINTMENTS
# ----------------------------
@app.get("/admin/view_appointments")
def admin_view_appointments(request: Request, db: Session = Depends(get_db)):
    appointments = db.query(Appointment).all()
    return templates.TemplateResponse(
    "view_appointments.html",
    {
    "request": request,
    "appointments": appointments,
    "source": "admin"
    }
    )
# ---------------- Admin Cancel Appointment ----------------
@app.get("/admin/cancel_appointment")
def admin_cancel_appointment_page(request: Request, db: Session = Depends(get_db)):
    appointments = crud.get_appointments(db)
    return templates.TemplateResponse(
    "cancel_appointment.html",
    {
    "request": request,
    "appointments": appointments,
    "form_action": "/admin/cancel_appointment?source=admin",  # ⬅ important
    "back_link": "/admin",
    "source": "admin"  # ⬅ tells HTML not to show OTP
    }
    )
@app.post("/admin/cancel_appointment")
def admin_cancel_appointment(
    request: Request,
    appointment_id: int = Form(...),
    db: Session = Depends(get_db)
    ):
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if appointment:
        appointment.status = "Cancelled"
        db.commit()
        message = f"Appointment ID {appointment_id} cancelled successfully!"
    else:
        message = f"No appointment found with ID {appointment_id}."
    appointments = crud.get_appointments(db)
    return templates.TemplateResponse(
    "cancel_appointment.html",
    {
    "request": request,
    "appointments": appointments,
    "form_action": "/admin/cancel_appointment?source=admin",  # ⬅ keep consistent
    "back_link": "/admin",
    "message": message,
    "source": "admin"  # ⬅ ensure OTP not shown
    }
    )
@app.get("/admin/view_cancelled")
def view_cancelled_appointments(request: Request, db: Session = Depends(get_db)):
# Fetch only cancelled appointments
    cancelled_appointments = db.query(Appointment).filter(Appointment.status == "Cancelled").all()
# Render your 'view_cancelled_appointments.html' template
    return templates.TemplateResponse(
    "view_cancelled_appointments.html",
    {
    "request": request,
    "appointments": cancelled_appointments
    }
    )
# GET route – show form & fetch doctor by ID
@app.get("/admin/edit_doctor")
def edit_doctor_page(request: Request, doctor_id: int = None, db: Session = Depends(get_db)):
    doctor = None
    message = None
    if doctor_id:
        doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
     message = f"Doctor ID {doctor_id} not found."
    return templates.TemplateResponse(
    "edit_doctor.html",
    {"request": request, "doctor": doctor, "message": message}
    )
# POST route – update doctor details
@app.post("/admin/update_doctor")
def update_doctor(
    request: Request,
    doctor_id: int = Form(...),
    name: str = Form(""),
    specialization: str = Form(""),
    db: Session = Depends(get_db)
    ):
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if doctor:
        if name.strip():
            doctor.name = name.strip()
        if specialization.strip():
            doctor.specialization = specialization.strip()
        db.commit()
        message = f"✅ Doctor ID {doctor_id} updated successfully."
    else:
        message = f"❌ Doctor ID {doctor_id} not found."
    return templates.TemplateResponse(
        "edit_doctor.html",
        {"request": request, "doctor": doctor, "message": message}
    )

# ---------------- Admin Edit Patient ----------------
@app.get("/admin/edit_patient")
def edit_patient_page(request: Request, patient_id: int = None, db: Session = Depends(get_db)):
    patient = None
    message = None
    if patient_id:
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        message = f"Patient ID {patient_id} not found."
    return templates.TemplateResponse(
        "edit_patient.html",
        {"request": request, "patient": patient, "message": message}
    )
@app.post("/admin/update_patient")
def update_patient(
    request: Request,
    patient_id: int = Form(...),
    name: str = Form(""),
    age: str = Form(""),
    gender: str = Form(""),
    dob: str = Form(""),
    contact: str = Form(""),
    symptoms: str = Form(""),
    db: Session = Depends(get_db)
):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if patient:
        if name.strip():
            patient.name = name.strip()
        if age.strip():
            patient.age = int(age)
        if gender.strip():
            patient.gender = gender.strip().title()
        if dob.strip():
            patient.dob = dob
        if contact.strip():
            patient.contact = contact.strip()
        if symptoms.strip():
            patient.symptoms = symptoms.strip()
        
        db.commit()
        message = f"✅ Patient ID {patient_id} updated successfully."
    else:
        message = f"❌ Patient ID {patient_id} not found."
    
    return templates.TemplateResponse(
        "edit_patient.html",
        {"request": request, "patient": patient, "message": message}
    )

# ------- Doctor Login -------
@app.get("/doctor/login", response_class=HTMLResponse)
def doctor_login_page(request: Request):
    return templates.TemplateResponse("doctor_login.html", {"request": request})


@app.post("/doctor/login")
def doctor_login(
    request: Request,
     username: str = Form(...), 
     password: str = Form(...), 
     db: Session = Depends(get_db)
):
    doctor = crud.authenticate_doctor(db, username, password)
    if doctor:
        request.session["doctor_id"] = doctor.id
        request.session["doctor_name"] = doctor.name
        return RedirectResponse("/doctor/dashboard", status_code=303)
    
    return templates.TemplateResponse(
        "doctor_login.html",
        {"request": request, "error": "Invalid username or password"}
    )
