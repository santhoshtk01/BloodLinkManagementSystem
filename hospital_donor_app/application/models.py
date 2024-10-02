from . import db
from datetime import datetime

class Donor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone_whatsapp = db.Column(db.String(20), unique=True, nullable=False)
    phone_contact = db.Column(db.String(20))
    location = db.Column(db.String(100))  # Latitude/longitude or address
    age = db.Column(db.Integer)
    blood_group = db.Column(db.String(3))
    gender = db.Column(db.String(10))
    weight = db.Column(db.Float)
    last_donated = db.Column(db.Date)
    medical_history = db.Column(db.Boolean, default=False)

class Hospital(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    unique_id = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100))
    address = db.Column(db.String(255))
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    pincode = db.Column(db.String(10))
    phone = db.Column(db.String(20))
    fax = db.Column(db.String(20))

class BloodRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospital.id'))
    blood_type = db.Column(db.String(3), nullable=False)
    units_requested = db.Column(db.Integer, nullable=False)
    urgency = db.Column(db.String(50))  # 'Immediate', 'Within a day'
    patient_name = db.Column(db.String(100))
    date_requested = db.Column(db.DateTime, default=datetime.utcnow)
    fulfilled = db.Column(db.Boolean, default=False)

class DonorResponse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    blood_request_id = db.Column(db.Integer, db.ForeignKey('blood_request.id'))
    donor_id = db.Column(db.Integer, db.ForeignKey('donor.id'))
    response = db.Column(db.String(10))  # 'ACCEPT' or 'REJECT'
    date_responded = db.Column(db.DateTime, default=datetime.utcnow)
