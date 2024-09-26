from flask import Blueprint
from .models import Donor
from flask import session
from .models import Hospital
from flask import render_template, request, redirect, url_for
from . import db
from .models import BloodRequest
from .utils import send_whatsapp_message, poll_for_responses
from flask import current_app, jsonify
import threading
import time


main = Blueprint('main', __name__)


# Function to fetch donor data based on WhatsApp number
def fetch_donor_by_whatsapp(whatsapp_number):
    # Query to fetch the donor where phone_whatsapp matches the provided number
    donor = Donor.query.filter_by(phone_whatsapp=whatsapp_number).first()

    # Check if the donor exists
    if donor:
        # Return or print the donor details
        return {
            'Name': donor.name,
            'Email': donor.email,
            'Phone (WhatsApp)': donor.phone_whatsapp,
            'Blood Group': donor.blood_group,
            'Location': donor.location,
            'Age': donor.age,  # Assuming age is a field in the model
            'Gender': donor.gender,  # Assuming gender is a field in the model
        }
    else:
        return f"No donor found with WhatsApp number {whatsapp_number}"


@main.route('/')
def home():
    return render_template('base.html')


@main.route('/register_donor', methods=['GET', 'POST'])
def register_donor():
    if request.method == 'POST':
        # Use request.form to handle form data for an HTML form
        data = request.form

        try:
            new_donor = Donor(
                name=data['name'],
                email=data['email'],
                phone_whatsapp=data['phone_whatsapp'],
                phone_contact=data['phone_contact'],
                location=data['location'],
                age=data['age'],
                blood_group=data['blood_group'],
                gender=data['gender'],
                weight=data['weight'],
                medical_history=data.get('medical_history') == 'on',  # Handle checkbox input
                last_donated=None  # Initially set to None
            )
            db.session.add(new_donor)
            db.session.commit()
            return render_template('login.html', success="Registered Successfully.")
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    return render_template('donor_registration.html', error="Invalid information.")


@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.form
        email_or_id = data.get('email_or_id')

        # Debugging: Check the form input value
        print(f"Attempting login with: {email_or_id}")

        # Check if it's a donor by email
        user = Donor.query.filter_by(email=email_or_id).first()
        if user:
            # Debugging: Confirm donor is found
            print(f"Donor found: {user.name}")

            # Set session values for donor
            session['logged_in'] = True
            session['role'] = 'donor'
            session['user_id'] = user.id

            # Redirect to donor dashboard
            print("Redirecting to donor dashboard...")
            return redirect(url_for('main.dashboard'))  # Ensure this line returns and exits the function

        # Check if it's a hospital by unique ID
        hospital = Hospital.query.filter_by(unique_id=email_or_id).first()
        if hospital:
            # Debugging: Confirm hospital is found
            print(f"Hospital found: {hospital.name}")

            # Set session values for hospital
            session['logged_in'] = True
            session['role'] = 'hospital'
            session['user_id'] = hospital.id

            # Redirect to hospital request blood form
            print("Redirecting to request blood form...")
            return redirect(url_for('main.request_blood'))  # Ensure this line returns and exits the function

        # If no donor or hospital is found, show invalid credentials
        print("Invalid credentials - No user or hospital found")
        return render_template('login.html',
                               error="Invalid credentials. Please try again.")  # This only executes if login fails

    return render_template('login.html')

from flask import current_app
import threading
import time

# Use a temporary list (or database/Redis) to store accepted donors
ACCEPTED_DONORS = []

@main.route('/request_blood', methods=['GET', 'POST'])
def request_blood():
    if request.method == 'POST':
        try:
            # Fetch form data
            blood_type = request.form['blood_type']
            units_requested = request.form['units_requested']
            urgency = request.form['urgency']
            patient_name = request.form['patient_name']

            # Create a new blood request object
            new_request = BloodRequest(
                blood_type=blood_type,
                units_requested=int(units_requested),
                urgency=urgency,
                patient_name=patient_name
            )
            db.session.add(new_request)
            db.session.commit()

            # Query for donors based on blood type
            matching_donors = Donor.query.filter_by(blood_group=blood_type).all()

            # Prepare the list of donors with WhatsApp numbers
            donor_list = [{'name': donor.name, 'whatsapp': donor.phone_whatsapp} for donor in matching_donors]
            print(f"Matching Donors: {donor_list}")

            # Send WhatsApp messages
            for donor in donor_list:
                send_whatsapp_message(donor['whatsapp'], patient_name, units_requested, blood_type)

            # Define the background thread function
            def poll_responses_thread(app):
                with app.app_context():  # Ensure the thread works within Flask app context
                    while True:
                        outputs = poll_for_responses()  # Poll for WhatsApp responses

                        for output in outputs:
                            # Fetch donor data by WhatsApp number
                            donor_data = fetch_donor_by_whatsapp(output)

                            if donor_data:
                                # Add donor to accepted list if they agreed
                                ACCEPTED_DONORS.append(donor_data)
                                print(f"Accepted Donors: {ACCEPTED_DONORS}")

                        # Sleep for some time before polling again
                        time.sleep(10)

            # Start the background polling thread with the current Flask app context
            polling_thread = threading.Thread(target=poll_responses_thread, args=(current_app._get_current_object(),))
            polling_thread.start()

            # Redirect or render the success page
            return render_template('blood_request.html', success=True, donors=donor_list)

        except Exception as e:
            print(f"Error: {e}")
            return "An error occurred while processing the request", 400

    # Render the form, passing success flag and donors list if available
    success = request.args.get('success', False)
    return render_template('blood_request.html', success=success, donors=None)


@main.route('/hospital_dashboard')
def hospital_dashboard():
    print("redirected to hospital dashboard")
    # Ensure the user is logged in as a hospital
    if 'logged_in' in session and session['role'] == 'hospital':
        try:
            # Fetch all blood requests (or restrict to requests created by the hospital)
            blood_requests = BloodRequest.query.all()

            # If you want to filter by the logged-in hospital, uncomment the next line:
            # blood_requests = BloodRequest.query.filter_by(hospital_id=session['user_id']).all()

            print(f"Blood requests: {blood_requests}")  # Debugging the query
        except Exception as e:
            print(f"Error fetching blood requests: {e}")
            return "Error fetching blood requests", 500  # Handle errors gracefully

        return render_template('hospital_dashboard.html', blood_requests=blood_requests)
    else:
        return redirect(url_for('main.login'))


@main.route('/dashboard')
def dashboard():
    print("redirected")
    # Ensure the user is logged in as a donor
    if 'logged_in' in session and session['role'] == 'donor':
        donor_id = session['user_id']  # Get the logged-in donor's ID
        try:
            # Fetch the logged-in donor's blood group
            donor = Donor.query.get(donor_id)
            if not donor:
                return "Donor not found", 404

            # Fetch only blood requests matching the donor's blood group
            matching_blood_requests = BloodRequest.query.filter_by(blood_type=donor.blood_group).all()

            print(f"Matching blood requests: {matching_blood_requests}")  # Debugging the query
        except Exception as e:
            print(f"Error fetching blood requests: {e}")
            return "Error fetching blood requests", 500  # Handle errors gracefully

        return render_template('dashboard.html', blood_requests=matching_blood_requests)
    else:
        return redirect(url_for('main.login'))


# Logout route
@main.route('/logout')
def logout():
    session.clear()  # Clear the session
    return redirect(url_for('main.login'))  # Redirect to login page

@main.route('/get_accepted_donors', methods=['GET'])
def get_accepted_donors():
    # Assuming ACCEPTED_DONORS is a global list or fetched from a database
    return jsonify(ACCEPTED_DONORS)

@main.route('/delete_request', methods=['POST'])
def delete_request():
    data = request.get_json()
    request_id = data.get('request_id')

    # Fetch the blood request by ID and delete it
    blood_request = BloodRequest.query.get(request_id)
    if blood_request:
        db.session.delete(blood_request)
        db.session.commit()
        return jsonify({"message": "Blood request marked as completed and removed."}), 200
    else:
        return jsonify({"error": "Blood request not found."}), 404

@main.route('/delete_donor', methods=['POST'])
def delete_donor():
    data = request.get_json()
    phone = data.get('phone')

    # Assuming ACCEPTED_DONORS is a global list or stored in a database
    global ACCEPTED_DONORS
    ACCEPTED_DONORS = [donor for donor in ACCEPTED_DONORS if donor['Phone (WhatsApp)'] != phone]

    return jsonify({"message": "Donor marked as contacted and removed."}), 200
