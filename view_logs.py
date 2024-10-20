import mysql.connector  # type: ignore
import time  # To create delays
import os  # To clear the screen

# Step 1: Connect to MySQL Database with autocommit enabled
db = mysql.connector.connect(
    host="localhost",  # Your database host
    user="root",  # Your MySQL username
    password="orangepi",  # Your MySQL password
    database="sys",  # Your database name
    autocommit=True  # Enable automatic commits to see real-time updates
)

# Step 2: Create a cursor to interact with the database
cursor = db.cursor()

# Step 3: Function to check server status (online/offline)
def check_server_status():
    try:
        db.ping(reconnect=True)  # Ping to check if server is up
        return "Server: Online"
    except:
        return "Server: Offline"

# Step 4: Function to fetch logs from the database
def fetch_logs():
    os.system('cls' if os.name == 'nt' else 'clear')  # Clear the screen (cmd/terminal)
    print(check_server_status())  # Show server status
    print("Real-time Entry Logs:")
    
    # Step 5: Run SQL to fetch the last 10 logs from `entry_logs` table
    cursor.execute("SELECT * FROM entry_logs ORDER BY entry_time DESC LIMIT 10")
    logs = cursor.fetchall()  # Get the logs

    # Step 6: Display each log line by line
    for log in logs:
        log_id, student_id, rfid_code, facial_recognition_status, entry_time = log
        print(f"Log ID: {log_id} | Student ID: {student_id} | RFID: {rfid_code} | Time: {entry_time}")

# Step 7: Main loop to refresh logs every 2 seconds
try:
    while True:
        fetch_logs()  # Show logs by re-running the SELECT query
        time.sleep(2)  # Wait 2 seconds before refreshing
except KeyboardInterrupt:
    print("Exiting...")  # Handle Ctrl+C exit
finally:
    cursor.close()  # Close connection
    db.close()  # Close connection
