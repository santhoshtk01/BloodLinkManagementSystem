from twilio.rest import Client
import time
from datetime import datetime, timedelta


ACCEPTED = []
final_numbers = []

# Twilio configuration
account_sid = 'AC87859f72dab00068c45ed144e8e0b90c'
auth_token = '43ff4b653c3b1357808a2eba65f89164'
client = Client(account_sid, auth_token)


# Function to extract the 10-digit phone number from the input
def extract_phone_number(phone_string):
    return phone_string[-10:]

def filter_last_10_seconds(accepted_list):
    # Get the current time (assumes 'Time' field in UTC)
    current_time = datetime.utcnow()

    # List to store filtered messages
    filtered_list = []

    for entry in accepted_list:
        # Parse the 'Time' field back into a datetime object
        message_time = datetime.strptime(entry['Time'], "%Y-%m-%d %H:%M:%S")

        # Check if the message time is within the last 10 seconds
        if current_time - message_time <= timedelta(seconds=15):
            filtered_list.append(entry)

    return filtered_list


def send_whatsapp_message(to_whatsapp, patient_name, units_requested, blood_type):
    from_whatsapp_number = 'whatsapp:+14155238886'
    message_body = (
        f"Patient {patient_name} needs {units_requested} units of {blood_type} blood.\n"
        f"Would you like to donate?\n"
        f"Reply with 'Yes' or 'No'."
    )
    message = client.messages.create(
        body=message_body,
        from_=from_whatsapp_number,
        to=f'whatsapp:+91{to_whatsapp}'
    )
    print(f"Message sent to {to_whatsapp} with SID: {message.sid}")


def poll_for_responses():
    final_numbers.clear()
    print("Polling for recent responses...")
    try:
        # Fetch incoming messages sent to the Twilio WhatsApp number
        messages = client.messages.list(to='whatsapp:+14155238886')

        for message in messages:
            if message.direction == 'inbound':
                # Check if the message body contains 'yes'
                if message.body.lower() == 'yes':
                    # Add the phone and reply time to the ACCEPTED list
                    ACCEPTED.append({
                        'Phone': message.from_,
                        'Time': message.date_sent.strftime("%Y-%m-%d %H:%M:%S")  # Format the reply time
                    })
        print(f"Accepted Donors: {filter_last_10_seconds(ACCEPTED)}")
    except Exception as e:
        print(f"Error fetching messages: {e}")

    for accept in filter_last_10_seconds(ACCEPTED):
        final_numbers.append(extract_phone_number(accept['Phone']))

    return final_numbers


def process_response(sender, body):
    # Process the message body to determine if it's a "Yes" or "No"
    body = body.strip().lower()
    if body in ['yes', 'y']:
        print(f"Donor {sender} agreed to donate!")
    elif body in ['no', 'n']:
        print(f"Donor {sender} declined to donate.")
    else:
        print(f"Received an unrecognized response from {sender}: {body}")


if __name__ == '__main__':
    while True:
        print(poll_for_responses())
        time.sleep(10)
