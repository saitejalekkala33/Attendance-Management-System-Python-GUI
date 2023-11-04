import cv2
import face_recognition
import json
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import os
import csv
import datetime

# Paths to data files
user_data_path = "faces.json"
attendance_file_path = "Attendance.csv"

# Load existing user data if available, or initialize an empty dictionary
if os.path.exists(user_data_path):
    with open(user_data_path, "r") as file:
        try:
            user_data = json.load(file)
        except json.JSONDecodeError:
            user_data = {}
else:
    user_data = {}

# Columns for the attendance CSV file
columns = ["Name", "Contact Number", "Employ ID"]

# Create the attendance CSV file if it doesn't exist
if not os.path.exists(attendance_file_path):
    with open(attendance_file_path, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(columns)

# Create the main Tkinter window
root = tk.Tk()
root.title("Face Recognition App")
root.geometry("800x600")

# Frames for different sections of the GUI
register_frame = tk.Frame(root)
recognize_frame = tk.Frame(root)
delete_frame = tk.Frame(root)

# Variable to keep track of the current displayed frame
current_frame = None

# Video capture from the default camera (0)
video_capture = cv2.VideoCapture(0)

# Function to show a frame in the GUI
def show_frame(frame):
    global current_frame
    if current_frame:
        current_frame.pack_forget()
    if frame.winfo_ismapped() == 0:
        frame.pack()
    current_frame = frame

# Function to display a message, hide entry fields, and a button
def display_message_and_hide_button1(message, name_entry, contact_entry, employ_id_entry, capture_button):
    messagebox.showinfo("Info", message)
    name_entry.pack_forget()
    contact_entry.pack_forget()
    employ_id_entry.pack_forget()
    capture_button.pack_forget()

# Variable to prevent multiple registration attempts
x = False

# Function to register a user through the GUI
def register_user_gui():
    global x
    if x:
        return 
    x = True
    show_frame(register_frame)

    # Entry fields for name, contact, and employee ID
    name_entry = tk.Entry(register_frame, width=40)
    name_entry.insert(0, "Enter your name")
    name_entry.pack()

    contact_entry = tk.Entry(register_frame, width=40)
    contact_entry.insert(0, "Enter your contact number")
    contact_entry.pack()

    employ_id_entry = tk.Entry(register_frame, width=40)
    employ_id_entry.insert(0, "Enter your employ ID")
    employ_id_entry.pack()

    # Functions to handle placeholder text
    def on_name_entry_click(event):
        if name_entry.get() == "Enter your name":
            name_entry.delete(0, tk.END)

    def on_contact_entry_click(event):
        if contact_entry.get() == "Enter your contact number":
            contact_entry.delete(0, tk.END)

    def on_employ_id_entry_click(event):
        if employ_id_entry.get() == "Enter your employ ID":
            employ_id_entry.delete(0, tk.END)

    name_entry.bind("<Button-1>", on_name_entry_click)
    contact_entry.bind("<Button-1>", on_contact_entry_click)
    employ_id_entry.bind("<Button-1>", on_employ_id_entry_click)

    # Function to capture the user's face
    def capture_face():
        global x
        ret, frame = video_capture.read()
        face_locations = face_recognition.face_locations(frame)

        if not face_locations:
            messagebox.showerror("Error", "No face detected. Please ensure your face is well-lit and visible.")
            x = False
            return
        elif len(face_locations) > 1:
            messagebox.showinfo("Info", "Multiple faces detected. Please ensure only one face is in the frame.")
            return

        face_encoding = face_recognition.face_encodings(frame, face_locations)[0]

        # Check for similar faces to prevent duplicate registrations
        for existing_user, user_info in user_data.items():
            existing_encoding = user_info.get("encoding")
            if existing_encoding is not None:
                distance = face_recognition.face_distance([existing_encoding], face_encoding)[0]
                if distance < 0.5:
                    display_message_and_hide_button1(f"Similar face already registered as {existing_user}. Skipping registration.", name_entry, contact_entry, employ_id_entry, capture_button)
                    x = False
                    return

        # Get user data
        name = name_entry.get()
        contact = contact_entry.get()
        employ_id = employ_id_entry.get()

        # Store user data in the JSON file
        user_data[name] = {
            "contact": contact,
            "employ_id": employ_id,
            "encoding": face_encoding.tolist()
        }

        with open(user_data_path, "w") as file:
            json.dump(user_data, file, indent=4)

        # Store user data in the CSV file
        with open('employ_details.csv', mode='a', newline='') as employ_file:
            employ_writer = csv.writer(employ_file)
            if employ_file.tell() == 0:
                employ_writer.writerow(["Name", "Contact Number", "Employ ID"])
            employ_writer.writerow([name, contact, employ_id])

        display_message_and_hide_button1(f"User {name} registered successfully!", name_entry, contact_entry, employ_id_entry, capture_button)
        x = False

    capture_button = tk.Button(register_frame, text="Capture Face", command=capture_face, width=20, height=2)
    capture_button.pack()

# Function to recognize a user through the GUI
def recognize_face():
    ret, frame = video_capture.read()
    face_locations = face_recognition.face_locations(frame)
    if not face_locations:
        messagebox.showinfo("Info", "No face detected.")
        return
    elif len(face_locations) > 1:
        messagebox.showinfo("Info", "Multiple faces detected. Please ensure only one face is in the frame.")
        return

    face_encoding = face_recognition.face_encodings(frame, face_locations)[0]

    recognized_user = None
    min_distance = 0.5

    # Find the recognized user with the smallest distance
    for name, user_info in user_data.items():
        registered_encoding = user_info["encoding"]
        distance = face_recognition.face_distance([registered_encoding], face_encoding)[0]

        if distance < min_distance:
            min_distance = distance
            recognized_user = name

    if recognized_user:
        # Get user contact and employee ID
        contact_info = user_data[recognized_user]['contact']
        employ_id_info = user_data[recognized_user]['employ_id']
        current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        
        # Read and update the attendance CSV file
        with open(attendance_file_path, "r") as file:
            reader = csv.DictReader(file)
            columns = reader.fieldnames
            rows = list(reader)
        
        date_in_column = f"{current_date} (IN)"
        date_out_column = f"{current_date} (OUT)"
        
        if date_in_column not in columns:
            columns.extend([date_in_column, date_out_column])
        
        found_user = False
        
        for row in rows:
            if row["Name"] == recognized_user:
                found_user = True
                if not row.get(date_in_column):
                    row[date_in_column] = datetime.datetime.now().strftime("%H:%M:%S")
                else:
                    row[date_out_column] = datetime.datetime.now().strftime("%H:M:S")
        
        if not found_user:
            new_row = {col: "" for col in columns}
            new_row["Name"] = recognized_user
            new_row["Contact Number"] = contact_info
            new_row["Employ ID"] = employ_id_info
            new_row[date_in_column] = datetime.datetime.now().strftime("%H:M:S")
            rows.append(new_row)
        
        with open(attendance_file_path, "w", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=columns)
            writer.writeheader()
            writer.writerows(rows)

        # Display recognized user information
        messagebox.showinfo("Info", f"Face matched with registered user: {recognized_user}\nContact: {contact_info}\nEmploy ID: {employ_id_info}")
    else:
        messagebox.showinfo("Info", "User not recognized")

# Function to save user data to the JSON file
def save_user_data(name, user_data):
    with open(user_data_path, "w") as file:
        json.dump(user_data, file, indent=4)

# Function to delete a registered face
def delete_face():
    ret, frame = video_capture.read()
    face_locations = face_recognition.face_locations(frame)
    if not face_locations:
        messagebox.showinfo("Info", "No face detected.")
        return
    elif len(face_locations) > 1:
        messagebox.showinfo("Info", "Multiple faces detected. Please ensure only one face is in the frame.")
        return

    face_encoding = face_recognition.face_encodings(frame, face_locations)[0]

    recognized_user = None

    for name, user_info in user_data.items():
        registered_encoding = user_info["encoding"]
        distance = face_recognition.face_distance([registered_encoding], face_encoding)[0]

        if distance < 0.5:
            recognized_user = name
            break

    if recognized_user:
        # Ask for confirmation before deleting user data
        confirmation = messagebox.askquestion("Confirm Deletion", f"Shall I delete the User {recognized_user}'s data?")
        if confirmation == "yes":
            del user_data[recognized_user]
            save_user_data(recognized_user, user_data)
            messagebox.showinfo("Info", f"User {recognized_user}'s data has been deleted.")
        else:
            messagebox.showinfo("Info", "Deletion canceled.")
        return
    messagebox.showinfo("Info", "User not recognized")

# Label to display video feed from the camera
video_label = tk.Label(root, width=400, height=300)
video_label.pack(side="left", padx=10, pady=10)

# Function to update the video feed
def update_video_frame():
    ret, frame = video_capture.read()
    if ret:
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = Image.fromarray(frame)
        frame = ImageTk.PhotoImage(image=frame)
        video_label.img = frame
        video_label.config(image=frame)
        video_label.after(10, update_video_frame)
    else:
        video_label.after(10, update_video_frame)

update_video_frame()

# Frame to hold buttons
button_frame = tk.Frame(root)
button_frame.pack(side="left", padx=10, pady=10)

# Buttons for various actions
register_button = tk.Button(root, text="Register a new user", command=register_user_gui, width=20, height=2)
register_button.pack(pady=10)

recognize_button = tk.Button(root, text="Recognize a user", command=recognize_face, width=20, height=2)
recognize_button.pack(pady=10)

delete_button = tk.Button(root, text="Delete a user", command=delete_face, width=20, height=2)
delete_button.pack(pady=10)

exit_button = tk.Button(root, text="Exit", command=root.quit, width=20, height=2)
exit_button.pack(pady=10)

# Start the main loop
root.mainloop()