import os
import numpy as np
import cv2
import mysql.connector
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Path to static sign images
SIGNS_FOLDER = os.path.join(app.root_path, "static", "signs")

# Database connection function
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Jayesh@45",
        database="signease"
    )

# Fetch sign images from database
def fetch_sign_images():
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("SELECT image_data, sign_name FROM sign_images")
    images = cursor.fetchall()
    db.close()
    return images

# Convert BLOB image data from database to an OpenCV image
def convert_blob_to_image(blob_data):
    image_array = np.frombuffer(blob_data, dtype=np.uint8)
    img = cv2.imdecode(image_array, cv2.IMREAD_GRAYSCALE)
    return img if img is not None else None

# Match uploaded image with stored sign images
def match_sign(uploaded_image):
    orb = cv2.ORB_create()
    uploaded_gray = cv2.cvtColor(uploaded_image, cv2.COLOR_BGR2GRAY)
    kp1, des1 = orb.detectAndCompute(uploaded_gray, None)
    
    if des1 is None or len(kp1) < 10:  # Ensure enough keypoints exist
        return None

    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    best_match = None
    best_score = 0
    MATCH_THRESHOLD = 50  # Set high to avoid false matches

    for blob, text in fetch_sign_images():
        db_image = convert_blob_to_image(blob)
        if db_image is None:
            continue
        
        kp2, des2 = orb.detectAndCompute(db_image, None)
        if des2 is None or len(kp2) < 10:
            continue
        
        matches = bf.match(des1, des2)
        score = len(matches)
        
        if score > best_score and score > MATCH_THRESHOLD:  # Ensure only strong matches
            best_score = score
            best_match = text
    
    return best_match if best_match else None

@app.route('/')
def index():
    return render_template("converter.html")

# Updated endpoint to handle multiple images
@app.route('/signtotext', methods=['POST'])
def sign_to_text():
    if 'files' not in request.files:
        return jsonify({"error": "No files provided"}), 400

    files = request.files.getlist('files')  # Get multiple files
    recognized_texts = []

    for file in files:
        if file.filename == '':
            continue

        file_bytes = np.frombuffer(file.read(), np.uint8)
        uploaded_image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

        if uploaded_image is None:
            continue

        recognized_text = match_sign(uploaded_image)
        recognized_texts.append(recognized_text)

    if not recognized_texts:
        return jsonify({"error": "No valid images processed"}), 400

    return jsonify({"text": " ".join(recognized_texts)})  # Join words together
    
if __name__ == "__main__":
    app.run(debug=True)

