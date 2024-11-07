import tkinter as tk
from tkinter import scrolledtext
import mysql.connector  # type: ignore
import time

db = mysql.connector.connect(
    host="localhost",
    user="root", 
    password="orangepi",  
    database="sys" 
)
cursor = db.cursor()

def get_student_id(rfid_code):
    sql = "SELECT student_id FROM rfid WHERE rfid_code = %s"
    cursor.execute(sql, (rfid_code,))
    result = cursor.fetchone()
    print(f"Searching for RFID: {rfid_code}, Result: {result}")  
    return result[0] if result else None 

def log_rfid_entry(rfid_data, log_display):
    student_id = get_student_id(rfid_data)
    if student_id is not None:
        sql = "INSERT INTO entry_logs (student_id, rfid_code, entry_time) VALUES (%s, %s, NOW())"
        cursor.execute(sql, (student_id, rfid_data))
        db.commit()
        log_display.insert(tk.END, f"Logged: {rfid_data} for Student ID: {student_id}\n")
    else:
        log_display.insert(tk.END, f"RFID code {rfid_data} not associated with any student.\n")

def create_gui():

    window = tk.Tk()
    window.title("RFID Logger System")
    window.geometry("600x400")

    log_display = scrolledtext.ScrolledText(window, width=70, height=20)
    log_display.grid(column=0, row=0, padx=10, pady=10)

    log_display.insert(tk.END, "RFID Logger System - Logs will appear here.\n")

    def read_rfid_input():
        while True:
            rfid_input = input("Scan an RFID... ") 
            log_rfid_entry(rfid_input.strip(), log_display) 

    import threading
    rfid_thread = threading.Thread(target=read_rfid_input, daemon=True)
    rfid_thread.start()

    window.mainloop()

if __name__ == "__main__":
    create_gui()

try:
    pass  
except KeyboardInterrupt:
    print("Exiting...")
finally:
    cursor.close()
    db.close()
