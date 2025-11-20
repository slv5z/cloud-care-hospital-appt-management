 # crud.py
from sqlalchemy.orm import Session
import models
from models import Patient, Doctor, Appointment
from datetime import datetime
import random


# ---------------------------------------------------------
#                     PATIENT CRUD
# ---------------------------------------------------------

def create_patient(db, name, age, gender, dob, contact, symptoms):
    """
    Create new patient — DOB conversion + 4-digit OTP generation.
    """
    dob_date = datetime.strptime(dob, "%Y-%m-%d").date()

    # ✅ Generate 4-digit OTP (0000–9999)
    otp_code = str(random.randint(0, 9999)).zfill(4)

    new_patient = Patient(
        name=name,
        age=age,
        gender=gender,
        dob=dob_date,
        contact=contact,
        symptoms=symptoms,
        otp_code=otp_code
    )

    db.add(new_patient)
    db.commit()
    db.refresh(new_patient)
    return new_patient


def get_patient(db: Session, patient_id: int):
    return db.query(Patient).filter(Patient.id == patient_id).first()


def get_patients(db: Session, search: str = None):
    """
    List all patients or filter by ID/name/contact.
    OTP is never hidden here, hiding happens in templates.
    """
    query = db.query(Patient)

    if search:
        like = f"%{search}%"
        if search.isdigit():
            query = query.filter(
                (Patient.id == int(search)) |
                (Patient.name.ilike(like)) |
                (Patient.contact.ilike(like))
            )
        else:
            query = query.filter(
                (Patient.name.ilike(like)) |
                (Patient.contact.ilike(like))
            )

    return query.order_by(Patient.id).all()


def search_patient(db: Session, term: str):
    return get_patients(db, search=term)


def update_patient(db: Session, patient_id: int, **kwargs):
    patient = get_patient(db, patient_id)
    if not patient:
        return None

    for key, value in kwargs.items():
        if key == "dob" and value:
            setattr(patient, key, datetime.strptime(value, "%Y-%m-%d").date())
        elif value is not None:
            setattr(patient, key, value)

    db.commit()
    db.refresh(patient)
    return patient


def delete_patient(db: Session, patient_id: int):
    patient = get_patient(db, patient_id)
    if not patient:
        return None

    db.delete(patient)
    db.commit()
    return patient


# ---------------------------------------------------------
#                     DOCTOR CRUD
# ---------------------------------------------------------

def create_doctor(db: Session, name: str, specialization: str):
    """
    Create doctor and auto-generate:
    username = doctor ID
    password = doctor_<id>
    """
    doctor = Doctor(name=name, specialization=specialization)

    db.add(doctor)
    db.flush()  # Assigns doctor.id

    # Auto-generate credentials
    doctor.username = str(doctor.id)
    doctor.password = f"doctor_{doctor.id}"

    db.commit()
    db.refresh(doctor)

    return doctor   # Never expose password in UI


def get_doctor(db: Session, doctor_id: int):
    return db.query(Doctor).filter(Doctor.id == doctor_id).first()


def get_doctors(db: Session, search: str = None):
    query = db.query(Doctor)
    if search:
        like = f"%{search}%"
        query = query.filter(Doctor.name.ilike(like))
    return query.all()


def update_doctor(db: Session, doctor_id: int, **kwargs):
    doctor = get_doctor(db, doctor_id)
    if not doctor:
        return None

    for key, value in kwargs.items():
        if value is not None:
            setattr(doctor, key, value)

    db.commit()
    db.refresh(doctor)
    return doctor


def delete_doctor(db: Session, doctor_id: int):
    doctor = get_doctor(db, doctor_id)
    if not doctor:
        return None

    db.delete(doctor)
    db.commit()
    return doctor

def search_doctor(db: Session, term: str):
    """
    Search doctors by:
    - ID (numeric)
    - Name
    - Specialization
    """
    query = db.query(Doctor)
    like = f"%{term}%"

    # If search term is a number: also check ID
    if term.isdigit():
        return query.filter(
            (Doctor.id == int(term)) |
            (Doctor.name.ilike(like)) |
            (Doctor.specialization.ilike(like))
        ).all()
    
    # If not a number: search by name or specialization
    return query.filter(
        (Doctor.name.ilike(like)) |
        (Doctor.specialization.ilike(like))
    ).all()





# ---------------------------------------------------------
#                     APPOINTMENTS CRUD
# ---------------------------------------------------------

def create_appointment(db: Session, patient_id: int, doctor_id: int, date: str, time: str):
    appointment_date = datetime.strptime(date, "%Y-%m-%d").date()
    appointment_time = datetime.strptime(time, "%H:%M").time()

    appointment = Appointment(
        patient_id=patient_id,
        doctor_id=doctor_id,
        appointment_date=appointment_date,
        appointment_time=appointment_time,
        status="Booked"
    )

    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return appointment


def get_appointment(db: Session, appointment_id: int):
    return db.query(Appointment).filter(Appointment.id == appointment_id).first()


def get_appointments(db: Session, search: str = None, include_cancelled: bool = False):
    query = db.query(Appointment)

    if not include_cancelled:
        query = query.filter(Appointment.status != "Cancelled")

    if search:
        like = f"%{search}%"
        query = query.filter(
            (Appointment.id.like(like)) |
            (Appointment.patient_id.like(like)) |
            (Appointment.doctor_id.like(like)) |
            (Appointment.appointment_date.like(like)) |
            (Appointment.appointment_time.like(like))
        )

    return query.all()


def update_appointment_status(db: Session, appointment_id: int, status: str):
    appointment = get_appointment(db, appointment_id)
    if not appointment:
        return None

    appointment.status = status
    db.commit()
    db.refresh(appointment)
    return appointment


def delete_appointment(db: Session, appointment_id: int):
    appointment = get_appointment(db, appointment_id)
    if not appointment:
        return None

    db.delete(appointment)
    db.commit()
    return appointment

def get_appointments_for_doctor(db: Session, doctor_id: int):
    return db.query(Appointment).filter(
        Appointment.doctor_id == doctor_id,
        Appointment.status != "Cancelled"
    ).all()



# ---------------------------------------------------------
#                OTP VERIFICATION (PATIENT)
# ---------------------------------------------------------

def get_patient_otp(db: Session, patient_id: int, entered_otp: str):
    """
    Returns True only if OTP matches.
    """
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        return False
    return patient.otp_code == entered_otp


def authenticate_doctor(db, username, password):
    return db.query(models.Doctor).filter(
        models.Doctor.username == username,
        models.Doctor.password == password
    ).first()
