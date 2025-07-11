from flask import Blueprint, Flask, request, render_template, redirect, url_for, jsonify, send_from_directory
import mysql.connector
import os
from werkzeug.utils import secure_filename



profile_bp = Blueprint('profile', __name__)

# Configure MySQL connection
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Jayesh@45',
    'database': 'signease'
}






# Profile Route (Handles GET and POST)
@profile_bp.route('/profile', methods=['GET', 'POST'])
def profile():
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name')
        contact = request.form.get('contact')
        email = request.form.get('email')
        member_since = request.form.get('member_since')
        dob = request.form.get('dob')
        alt_email = request.form.get('alt_email')
        
        # Handle profile picture upload
        profile_pic = request.files.get('profile_pics')
        profile_pic_filename = None
        profile_pic_blob = None
        
        if profile_pic:
            profile_pic_filename = secure_filename(f"{email}_profile.png")
            profile_pic_path = os.path.join(profile_bp.config['UPLOAD_FOLDER'], profile_pic_filename)
            profile_pic.save(profile_pic_path)  # Save file to folder
            
            # Convert image to binary (BLOB) for storing in MySQL
            with open(profile_pic_path, 'rb') as file:
                profile_pic_blob = file.read()

        # Connect to MySQL
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Insert data into MySQL
        cursor.execute("""
            INSERT INTO users (name, contact, email, member_since, dob, alt_email, profile_pics, profile_pic_blob) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (name, contact, email, member_since, dob, alt_email, profile_pic_filename, profile_pic_blob))

        conn.commit()
        cursor.close()
        conn.close()

        # Redirect to dashboard after saving profile
        return redirect(url_for('dashboard_page'))

    return render_template('profile.html')

# Route to fetch user profile data (JSON Response)
@profile_bp.route('/get-profile/<email>', methods=['GET'])
def get_profile(email):
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    user_data = cursor.fetchone()
    
    cursor.close()
    conn.close()

    if user_data:
        return jsonify(user_data)
    return jsonify({'error': 'User not found'}), 404

# Dashboard Route (Dummy Route)
@profile_bp.route('/dashboard')
def dashboard_page():
    return "<h1>Welcome to Dashboard</h1>"

if __name__ == '__main__':
    profile_bp.run(debug=True)
