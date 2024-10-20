import cv2 
import face_recognition 
import numpy as np 
import os

# Path where facial recognition data is stored (e.g., known faces)
KNOWN_FACES_DIR = "known_faces"
TOLERANCE = 0.6  # Lower means stricter matching
FRAME_THICKNESS = 3
FONT_THICKNESS = 2
MODEL = "cnn"  # Convolutional Neural Network model for face detection

# Load known faces and names
print("Loading known faces...")
known_faces = []
known_names = []

for name in os.listdir(KNOWN_FACES_DIR):
    for filename in os.listdir(f"{KNOWN_FACES_DIR}/{name}"):
        image = face_recognition.load_image_file(f"{KNOWN_FACES_DIR}/{name}/{filename}")
        encoding = face_recognition.face_encodings(image)[0]
        known_faces.append(encoding)
        known_names.append(name)

# This function starts the camera and tries to recognize faces
def recognize_face():
    print("Starting webcam for facial recognition...")
    video_capture = cv2.VideoCapture(0)

    while True:
        ret, frame = video_capture.read()

        # Resize the frame for faster processing
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = small_frame[:, :, ::-1]

        # Find all face locations and face encodings in the current frame of video
        face_locations = face_recognition.face_locations(rgb_small_frame, model=MODEL)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        for face_encoding, face_location in zip(face_encodings, face_locations):
            # See if the face is a match for known faces
            matches = face_recognition.compare_faces(known_faces, face_encoding, TOLERANCE)
            name = "Unknown"

            # Use the known face with the smallest distance to the new face
            face_distances = face_recognition.face_distance(known_faces, face_encoding)
            best_match_index = np.argmin(face_distances)
            if matches[best_match_index]:
                name = known_names[best_match_index]

            print(f"Detected: {name}")

            # If a match is found, return the name
            if name != "Unknown":
                video_capture.release()
                cv2.destroyAllWindows()
                return name

        # Display the resulting frame with annotations (optional for testing)
        for (top, right, bottom, left), name in zip(face_locations, known_names):
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4

            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), FRAME_THICKNESS)
            cv2.putText(frame, name, (left + 6, bottom - 6), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), FONT_THICKNESS)

        # Show the frame for debugging purposes
        cv2.imshow('Video', frame)

        # Quit video feed by pressing 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Release handle to the webcam
    video_capture.release()
    cv2.destroyAllWindows()

# This function verifies the face based on the given RFID data
def facial_recognition_verification(rfid_user):
    print(f"Starting facial recognition verification for RFID user: {rfid_user}")
    detected_face = recognize_face()

    if detected_face == rfid_user:
        print("Facial recognition passed.")
        return True
    else:
        print("Facial recognition failed.")
        return False
