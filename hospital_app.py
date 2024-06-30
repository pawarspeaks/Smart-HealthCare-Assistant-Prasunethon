import streamlit as st
from pymongo import MongoClient
from bson.objectid import ObjectId
import uuid
import pandas as pd
from streamlit_cookies_manager import EncryptedCookieManager
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Initialize cookies manager with a password
password = "your_secret_password"  # Replace with a secure password
cookies = EncryptedCookieManager(
    password=password, 
    prefix="app"
)

# MongoDB Connection
client = MongoClient('mongodb+srv://atharva2021:123@cluster0.so5reec.mongodb.net/')
db = client['HospitalManagement']
raisedappointment_collection = db['raisedappointment']
approveduser_collection = db['approveduser']
organization_collection = db['organization']  # Assuming this collection exists for organization details

# Function to fetch organization details
def get_organization_details(org_name):
    return organization_collection.find_one({"organization_name": org_name})

# Function to fetch organization details based on admin email
def get_organization_details_by_email(admin_email):
    return organization_collection.find_one({"admin_email": admin_email})

# Function to approve an appointment and notify user via email
def approve_appointment(appointment_id):
    appointment = raisedappointment_collection.find_one({"_id": ObjectId(appointment_id)})
    if appointment:
        appointment["Status"] = "Approved"
        approveduser_collection.insert_one(appointment)
        raisedappointment_collection.delete_one({"_id": ObjectId(appointment_id)})
        st.success("Appointment approved and moved to approveduser collection")

        # Notify patient via email
        send_notification_email(appointment['Email'], "Appointment Approved", f"Dear User, Greetings from Smart-HealthCare-Assistance.Your appointment with {appointment['Doctor Name']} on {appointment['Appointment Date']} at {appointment['Appointment Time']} has been approved.")

    else:
        st.error("Appointment not found")

# Function to disapprove an appointment and notify user via email
def disapprove_appointment(appointment_id):
    appointment = raisedappointment_collection.find_one({"_id": ObjectId(appointment_id)})
    if appointment:
        raisedappointment_collection.update_one(
            {"_id": ObjectId(appointment_id)},
            {"$set": {"Status": "Disapproved"}}
        )
        st.success("Appointment disapproved")

        # Notify patient via email
        send_notification_email(appointment['Email'], "Appointment Disapproved", f"Dear User, Greetings from Smart-HealthCare-Assistance.Your appointment request with {appointment['Doctor Name']} on {appointment['Appointment Date']} at {appointment['Appointment Time']} has been disapproved.")
    else:
        st.error("Appointment not found")

# Function to send email notification
def send_notification_email(to_email, subject, message):
    from_email = 'odop662@gmail.com'
    email_pass = 'zykvuppkoznmpgzn'

    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(message, 'plain'))

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(from_email, email_pass)
    text = msg.as_string()
    server.sendmail(from_email, to_email, text)
    server.quit()

# Function to add a new doctor
def add_doctor(org_name, doctor_data):
    result = organization_collection.update_one(
        {"organization_name": org_name},
        {"$push": {"doctors": doctor_data}}
    )
    if result.modified_count > 0:
        st.success("Doctor added successfully")
    else:
        st.error("Failed to add doctor")

# Function to update a doctor's details
def update_doctor(org_name, doctor_id, new_data):
    result = organization_collection.update_one(
        {"organization_name": org_name, "doctors.doctor_id": doctor_id},
        {"$set": {"doctors.$": new_data}}
    )
    if result.modified_count > 0:
        st.success("Doctor details updated")
    else:
        st.error("Failed to update doctor details")

# Function to delete a doctor
def delete_doctor(org_name, doctor_id):
    result = organization_collection.update_one(
        {"organization_name": org_name},
        {"$pull": {"doctors": {"doctor_id": doctor_id}}}
    )
    if result.modified_count > 0:
        st.success("Doctor deleted successfully")
    else:
        st.error("Failed to delete doctor")

# Function to save user session
def save_user_session(username):
    cookies["user"] = username
    cookies["token"] = generate_token()
    cookies.save()

# Function to load user session
def load_user_session():
    return cookies.get("user"), cookies.get("token")

# Function to clear session (logout)
def clear_session():
    cookies["user"] = ""
    cookies.save()

# Function to generate token
def generate_token():
    return str(uuid.uuid4())

# Streamlit Pages
def main():
    st.title("Hospital Appointment Management")

    # Check if user is logged in
    if "user" not in cookies or "token" not in cookies or cookies["user"] == "" or cookies["token"] == "":
        st.subheader("Organization Login")
        admin_email = st.text_input("Admin Email")
        password = st.text_input("Password", type='password')
        if st.button("Login"):
            # Validate organization login
            org_data = get_organization_details_by_email(admin_email)
            if org_data:
                stored_password = org_data.get("password", "")
                if password == stored_password:
                    st.success(f"Logged in as {org_data['organization_name']}")
                    save_user_session(org_data['organization_name'])
                else:
                    st.error("Invalid credentials")
            else:
                st.error("Organization not found")
        return

    # Fetch organization name from session
    org_name, _ = load_user_session()
    org_data = get_organization_details(org_name)

    if org_data:
        st.subheader(f"Logged in as {org_name}")

        # Menu options
        menu = ["Approve or Disapprove Appointments", "View Approved Appointments", "Manage Doctors", "View Organization Profile", "Logout"]
        choice = st.sidebar.selectbox("Menu", menu)

        # Handle menu choices
        if choice == "Approve or Disapprove Appointments":
            st.subheader("Approve or Disapprove Appointments")
            st.markdown("---")

            appointments = list(raisedappointment_collection.find({"Status": "Pending"}))

            if appointments:
                for appointment in appointments:
                    st.markdown(f"**Appointment ID:** {appointment['_id']}")
                    st.markdown(f"**Organization Name:** {appointment['Organization Name']}")
                    st.markdown(f"**Doctor Name:** {appointment['Doctor Name']}")
                    st.markdown(f"**Appointment Date:** {appointment['Appointment Date']}")
                    st.markdown(f"**Appointment Time:** {appointment['Appointment Time']}")
                    st.markdown(f"**Patient Email:** {appointment['Email']}")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"Approve {appointment['_id']}"):
                            approve_appointment(appointment['_id'])
                    with col2:
                        if st.button(f"Disapprove {appointment['_id']}"):
                            disapprove_appointment(appointment['_id'])
                    st.markdown("---")
            else:
                st.write("No pending appointments.")

        elif choice == "View Approved Appointments":
            st.subheader("View Approved Appointments")
            approved_appointments = list(approveduser_collection.find({}))

            if approved_appointments:
                df = pd.DataFrame(approved_appointments)
                df = df.drop(columns=['_id'])
                st.dataframe(df)
            else:
                st.write("No approved appointments.")

        elif choice == "Manage Doctors":
            st.subheader("Manage Doctors")

            # Option to add a new doctor
            st.subheader("Add New Doctor")
            new_doctor_id = st.text_input("Doctor ID")
            new_doctor_name = st.text_input("Doctor Name")
            new_doctor_education = st.text_input("Doctor Education")
            new_doctor_experience = st.number_input("Doctor Experience", min_value=0, step=1)
            new_doctor_specialist = st.text_input("Doctor Specialist")
            if st.button("Add Doctor"):
                new_doctor_data = {
                    "doctor_id": new_doctor_id,
                    "doctor_name": new_doctor_name,
                    "doctor_education": new_doctor_education,
                    "doctor_experience": new_doctor_experience,
                    "doctor_specialist": new_doctor_specialist
                }
                add_doctor(org_name, new_doctor_data)

            # Option to manage existing doctors
            st.subheader("Manage Existing Doctors")

            doctor_names = [doctor['doctor_name'] for doctor in org_data.get("doctors", [])]
            selected_doctor_name = st.selectbox("Select Doctor", doctor_names)

            if selected_doctor_name:
                selected_doctor = next((doctor for doctor in org_data["doctors"] if doctor["doctor_name"] == selected_doctor_name), None)
                if selected_doctor:
                    st.write(f"**Doctor ID:** {selected_doctor['doctor_id']}")
                    st.write(f"**Doctor Name:** {selected_doctor['doctor_name']}")
                    st.write(f"**Specialist:** {selected_doctor['doctor_specialist']}")
                    st.write(f"**Education:** {selected_doctor['doctor_education']}")
                    st.write(f"**Experience:** {selected_doctor['doctor_experience']} years")

                    st.subheader("Update Doctor Details")
                    updated_name = st.text_input("Updated Doctor Name", value=selected_doctor["doctor_name"])
                    updated_specialist = st.text_input("Updated Specialist", value=selected_doctor["doctor_specialist"])
                    updated_education = st.text_input("Updated Education", value=selected_doctor["doctor_education"])
                    updated_experience = st.number_input("Updated Experience", value=selected_doctor["doctor_experience"], min_value=0, step=1)

                    if st.button("Update Doctor"):
                        updated_data = {
                            "doctor_id": selected_doctor["doctor_id"],
                            "doctor_name": updated_name,
                            "doctor_specialist": updated_specialist,
                            "doctor_education": updated_education,
                            "doctor_experience": updated_experience
                        }
                        update_doctor(org_name, selected_doctor["doctor_id"], updated_data)

                    st.subheader("Delete Doctor")
                    if st.button("Delete Doctor"):
                        delete_doctor(org_name, selected_doctor["doctor_id"])

        elif choice == "View Organization Profile":
            st.subheader("View Organization Profile")
            st.write(org_data)

        elif choice == "Logout":
            clear_session()
            st.success("Logged out successfully")
            st.experimental_rerun()

if __name__ == '__main__':
    main()
