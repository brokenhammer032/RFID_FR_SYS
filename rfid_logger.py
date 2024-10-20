import tkinter as tk
from tkinter import scrolledtext
from datetime import datetime
from tkinter import messagebox
import mysql.connector  # type: ignore
import time
import getpass 
import threading
import os
import socket
import colorama # type: ignore
from colorama import Fore, Style # type: ignore

try:
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="orangepi",
        database="sys"
    )
    cursor = db.cursor()
except mysql.connector.Error as err:
    print(f"Error: {err}")
    exit(1)

SYSTEM_PASSCODE = "1234"
MAX_ATTEMPTS = 3  # Max failed RFID attempts before lockout
failed_attempts = 0  # Counter for failed attempts

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("RFID Logger")
        self.root.configure(bg="#f0f0f0") 

        self.current_students = []

        # Frame for the main content
        main_frame = tk.Frame(root, bg="#f0f0f0", padx=20, pady=20)
        main_frame.pack(padx=10, pady=10)

        # Display for the number of students inside
        self.count_display = tk.Label(main_frame, text="Number of Students Inside: 0", font=("Arial", 16), bg="#f0f0f0")
        self.count_display.pack(pady=10)

        # Display for the current students
        self.student_display = scrolledtext.ScrolledText(main_frame, width=60, height=15, font=("Arial", 12), bg="#e6e6e6")
        self.student_display.pack(pady=10)
        self.student_display.insert(tk.END, "Current Students Inside:\n")

        # RFID input field
        self.rfid_var = tk.StringVar()
        self.rfid_var.trace_add("write", self.process_rfid_input)
        self.rfid_entry = tk.Entry(main_frame, textvariable=self.rfid_var, width=50, font=("Arial", 14), bg="#ffffff")
        self.rfid_entry.pack(pady=10)
        self.rfid_entry.insert(0, "")
        self.rfid_entry.bind("<Return>", self.process_rfid_input)

        # Frame for crash simulation buttons (hidden by default)
        self.crash_button_frame = tk.Frame(root, bg="#f0f0f0")
        self.crash_button_frame.pack(pady=10)
        self.crash_button_frame.pack_forget()  # Hide by default

        #tk.Button(self.crash_button_frame, text="Simulate DB Crash", command=simulate_db_crash).pack(side="left", padx=5)
        #tk.Button(self.crash_button_frame, text="Simulate App Crash", command=simulate_app_crash).pack(side="left", padx=5)
        #tk.Button(self.crash_button_frame, text="Simulate Freeze", command=simulate_freeze).pack(side="left", padx=5)
        #tk.Button(self.crash_button_frame, text="Simulate Network Failure", command=simulate_network_failure).pack(side="left", padx=5)

        self.update_student_list()

    def process_rfid_input(self, *args):  # Fixed method
        """Process RFID input."""
        rfid_input = self.rfid_entry.get().strip()
        if rfid_input and rfid_input != "Enter RFID code here...":
            handle_rfid_scan(rfid_input, self.student_display)
            self.rfid_entry.delete(0, tk.END)

    def update_student_list(self):
        """Fetch current students inside and update the display."""
        self.current_students = get_current_students_info()

        self.count_display.config(text=f"Number of Students Inside: {len(self.current_students)}")

        self.student_display.delete(1.0, tk.END)
        self.student_display.insert(tk.END, "Current Students Inside:\n")
        for student in self.current_students:
            self.student_display.insert(tk.END, f"ID: {student['id']}, Name: {student['name']}, Entry Time: {student['entry_time'].strftime('%I:%M %p')}\n")

        self.root.after(5000, self.update_student_list)

    def show_crash_simulations(self):
        """Display crash simulation buttons after correct passcode."""
        self.crash_button_frame.pack()  

    def log_event(event):
        """Logs events to a file for monitoring."""
        with open("system_log.txt", "a") as log_file:
            log_file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {event}\n")

def authenticate_passcode(root):
    """Prompt for passcode to unlock system."""
    passcode_window = tk.Toplevel(root)
    passcode_window.title("Enter Passcode")
    passcode_window.geometry("300x150")
    
    tk.Label(passcode_window, text="Enter Passcode:", font=("Arial", 12)).pack(pady=10)
    passcode_entry = tk.Entry(passcode_window, show="*", font=("Arial", 12), width=20)
    passcode_entry.pack(pady=10)

    def verify_passcode():
        if passcode_entry.get() == SYSTEM_PASSCODE:
            messagebox.showinfo("Access Granted", "Correct passcode!")
            passcode_window.destroy()
        else:
            messagebox.showerror("Access Denied", "Incorrect passcode.")

    tk.Button(passcode_window, text="Submit", command=verify_passcode).pack(pady=5)
    
    passcode_window.transient(root)
    passcode_window.grab_set()
    root.wait_window(passcode_window)

def get_student_info(rfid_data):
    """Fetch student information based on the RFID data."""
    try:
        print(f"Searching for RFID: {rfid_data}")

        sql_query = "SELECT student_id FROM rfid WHERE rfid_code = %s"
        cursor.execute(sql_query, (rfid_data,))
        result = cursor.fetchone()

        if result:
            student_id = result[0]
            print(f"Found student_id: {student_id} for RFID: {rfid_data}")

            sql_query_details = "SELECT student_id, name FROM students WHERE student_id = %s"
            cursor.execute(sql_query_details, (student_id,))
            student_info = cursor.fetchone()
            print(f"Retrieved student info: {student_info}")
            return student_info  

        else:
            print("No matching RFID found.")
            return None  
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

def get_current_students_info():
    """Fetch the current students inside the campus from the database."""
    students_info = []
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="orangepi",
            database="sys"
        )
        cursor = connection.cursor()
        cursor.execute("""
            SELECT s.student_id, s.name, a.entry_time 
            FROM students s 
            JOIN active_students a ON s.student_id = a.student_id
        """)
        results = cursor.fetchall()

        for student_id, name, entry_time in results:
            students_info.append({
                'id': student_id,
                'name': name,
                'entry_time': entry_time
            })
    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        cursor.close()
        connection.close()

    return students_info

def log_rfid_entry(rfid_data, log_display):
    print(f"Attempting to log RFID entry for: {rfid_data}")  # Debug statement
    student_info = get_student_info(rfid_data)
    if student_info is not None:
        student_id, student_name = student_info

        sql_check = "SELECT entry_time FROM active_students WHERE student_id = %s"
        cursor.execute(sql_check, (student_id,))
        active_record = cursor.fetchone()

        if active_record:  
            entry_time = active_record[0]
            exit_time = datetime.now()

            formatted_entry_time = entry_time.strftime('%I:%M %p')
            formatted_exit_time = exit_time.strftime('%I:%M %p')

            sql_log = """
                INSERT INTO entry_logs (student_id, rfid_code, entry_time, exit_time, facial_recognition_status)
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(sql_log, (student_id, rfid_data, entry_time, exit_time, False))
            db.commit()

            sql_remove = "DELETE FROM active_students WHERE student_id = %s"
            cursor.execute(sql_remove, (student_id,))
            db.commit()

            log_display.insert(tk.END, f"TAP OUT: {student_id} - {student_name}\nEntry Time: {formatted_entry_time}\nExit Time: {formatted_exit_time}\n\n")
        else:
            entry_time = datetime.now()

            sql_insert = "INSERT INTO active_students (student_id, rfid_code, entry_time) VALUES (%s, %s, %s)"
            cursor.execute(sql_insert, (student_id, rfid_data, entry_time))
            db.commit()

            formatted_entry_time = entry_time.strftime('%I:%M %p')

            log_display.insert(tk.END, f"TAP IN: {student_id} - {student_name}\nEntry Time: {formatted_entry_time}\n\n")
    else:
        log_display.insert(tk.END, f"Unknown RFID: {rfid_data}\n\n")

def handle_rfid_scan(rfid_code, log_display):
    """Handle RFID scanning process with failsafe for multiple failures."""
    global failed_attempts
    if get_student_info(rfid_code):  # Valid RFID
        log_rfid_entry(rfid_code, log_display)
        failed_attempts = 0  # Reset on valid scan
    else:
        failed_attempts += 1
        log_display.insert(tk.END, f"Invalid RFID: {rfid_code}\n\n")
        if failed_attempts >= MAX_ATTEMPTS:
            system_lockout()

def system_lockout():
    """Handle system lockout and bring up the passcode prompt."""
    messagebox.showwarning("System Lockout", "system failure. Returning to passcode lock.")
       
        # Show a lockout message in the GUI
    lockout_label = tk.Label(root, text="System Lockout: Unauthorized Access", fg="red", font=("Arial", 14))
    lockout_label.pack(pady=20)
        # Disable inputs (like scanning)
    log_rfid_entry(state=tk.DISABLED)

    authenticate_passcode(root)  # Re-authenticate by returning to the passcode screen

# Crash simulation functions
colorama.init()

def simulate_db_crash():
    """Simulate a database connection crash."""
    try:
        cursor.close()
        db.close()
        print("Database connection closed. Simulating crash.")
        messagebox.showerror("Database Error", "Database connection lost. Returning to passcode lock.")
        system_lockout()  # Trigger system lockout after crash
    except Exception as e:
        print(f"Error simulating crash: {e}")
        system_lockout()  # Ensure lockout happens even in case of error

def simulate_app_crash():
    """Simulate an application crash by forcefully exiting."""
    print("Simulating a system crash...")
    system_lockout()  # Trigger system lockout after crash

def simulate_freeze():
    """Simulate a system freeze by creating an infinite loop."""
    print("Simulating a system freeze...")
    system_lockout()  # Trigger system lockout after freeze

def simulate_freeze():
    """Simulate a system freeze by creating an infinite loop."""
    print("Simulating a system freeze...")
    while True:
        pass  # Infinite loop to simulate system freeze

def simulate_network_failure():
    """Simulate network failure by inducing a timeout."""
    try:
        # Simulate network timeout by connecting to a nonexistent server
        s = socket.create_connection(("10.255.255.1", 9999), timeout=5)
    except (socket.timeout, socket.error):
        messagebox.showerror("Network Error", "Network failure. Please check your connection.")
        print("Simulating network failure...")

def simulate_cmd_system_crash():
    print(Fore.GREEN + "Starting system status check..." + Style.RESET_ALL)
    
    # System components to simulate
    components = [
        {"name": "Database", "details": ["Tables", "Indexes", "Views", "Triggers"]},
        {"name": "RFID System", "details": ["Reader 1", "Reader 2", "Security Protocol"]},
        {"name": "Program", "details": ["Main Process", "Logging Service", "User Interface"]},
        {"name": "SMS Service", "details": ["Message Queue", "SMS Gateway"]},
        {"name": "Authentication System", "details": ["Facial Recognition", "RFID Verification"]},
        {"name": "Web Server", "details": ["HTTP Server", "API Endpoints"]},
    ]

    # Display initial "All systems operational" status
    for component in components:
        print(Fore.GREEN + f"{component['name']} Status: Operational")
        for detail in component['details']:
            print(Fore.GREEN + f"    - {detail}: Online" + Style.RESET_ALL)
        time.sleep(.5)

    print("\n" + Fore.YELLOW + "All systems operational. Database loading..." + Style.RESET_ALL)
    time.sleep(1)

   
    #for component in components:
    #    print(Fore.RED + f"{component['name']} Status: Offline")
    #    for detail in component['details']:
    #       time.sleep(0.5)
    #       print(Fore.RED + f"    - {detail}: Crashed" + Style.RESET_ALL)

    # Final crash message
    #print("\n" + Fore.RED + "Database Compromised. System rebooting" + Style.RESET_ALL)

if __name__ == "__main__":
    simulate_cmd_system_crash()


# Main code execution
if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    authenticate_passcode(root)  # Ask for passcode first
    root.mainloop()
