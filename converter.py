from flask import Flask, render_template, request, jsonify, send_file
import os
import mysql.connector

app = Flask(__name__)

# MySQL Database Configuration
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Jayesh@45",
    "database": "signease"
}

SIGNS_FOLDER = "static/signs"  # Folder where signs are stored

def get_db_connection():
    """Establish connection to MySQL"""
    return mysql.connector.connect(**DB_CONFIG)

def get_sign_image(word):
    """Check if word sign exists in static folder or database"""
    image_filename = f"{word}.png"
    image_path = os.path.join(SIGNS_FOLDER, image_filename)

    if os.path.exists(image_path):
        return image_filename

    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("SELECT image_data FROM sign_images WHERE sign_name = %s", (word,))
    result = cursor.fetchone()
    db.close()

    return image_filename if result else None

@app.route('/')
def index():
    return render_template("converter.html")

@app.route('/text-to-sign', methods=['POST'])
def text_to_sign():
    data = request.get_json()
    text = data.get("text", "").strip().lower()
    words = text.split()

    images = []
    for word in words:
        img = get_sign_image(word)
        if img:
            images.append(img)  # Found word sign
        else:
            # Break into letters if word not found
            for letter in word:
                letter_img = get_sign_image(letter)
                if letter_img:
                    images.append(letter_img)

    if images:
        return jsonify({"images": images})
    return jsonify({"error": "Sign not found"}), 404

if __name__ == '__main__':
    app.run(debug=True)
