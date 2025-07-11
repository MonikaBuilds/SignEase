import datetime
import re
import sqlite3
from flask import Flask, jsonify, render_template, request, redirect, url_for, session, flash,send_from_directory
import os
import mysql.connector
import random
import smtplib
from email.mime.text import MIMEText
from werkzeug.security import generate_password_hash, check_password_hash
import cv2
import numpy as np
from profile_1 import profile_bp
from werkzeug.utils import secure_filename


from converter import get_sign_image
import profile_1

app = Flask(__name__)
app.secret_key = 'your_secret_key'

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Jayesh@45',
    'database': 'signease'
}

EMAIL_ADDRESS = "jayesh.d.chaudhary@slrtce.in"
EMAIL_PASSWORD = "vjkb ibzj vqdl vatu"

def send_otp(email, otp):
    subject = "Your OTP for Password Reset"
    body = f"Your OTP for resetting the password is: {otp}. Please do not share this OTP with anyone."
    
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = email

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, email, msg.as_string())
        return True
    except Exception as e:
        print("Error sending email:", e)
        return False

@app.route('/')
def welcome_page():
    return render_template('welcome.html')



@app.route('/signup', methods=['GET', 'POST'])
def signup():
    message = None
    status = None



    if request.method == 'POST':
        fullname = request.form['fullname']
        email = request.form['email']
        contactnumber = request.form['contactnumber']
        username = request.form['Username']
        password = request.form['password']
        confirmpassword = request.form['confirmpassword']

    

       
        if password != confirmpassword:
            flash("Passwords do not match! Please try again.", "danger")
            return redirect(url_for('signup'))
        
        if not contactnumber.isdigit() or len(contactnumber) != 10:
            flash("Phone number must be exactly 10 digits!", "danger")
            return redirect(url_for('signup'))
        
        hashed_password = generate_password_hash(password)

        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor()

            query = "INSERT INTO singup (fullname, email, contactnumber, Username, password, confirmpassword) VALUES (%s, %s, %s, %s, %s, %s)"
            cursor.execute(query, (fullname, email, contactnumber, username, password, confirmpassword))
            conn.commit()

            cursor.close()
            conn.close()
            flash("Signup successful! Please log in.", "success")
            return redirect(url_for('login_page'))
        except mysql.connector.Error as e:
            flash(f"Error: {e}", "danger")
    return render_template('signup.html')



@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor()

            
            query = "SELECT * FROM singup WHERE email = %s AND password = %s"
            cursor.execute(query, (email,password))
            user = cursor.fetchone()

            cursor.close()
            conn.close()

            if user:
              session['email'] = email  
              return jsonify({'status': 'success'})  
            else:
              return jsonify({'status': 'error', 'message': 'Invalid username or password. Please try again.'})

        except Exception as e:
                 return jsonify({'status': 'error', 'message': str(e)})

       
    return render_template('login.html')

@app.route('/dashboard')
def dashboard_page():
    if 'email' not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for('login_page'))
    return render_template('dashboard.html')


@app.route('/forgetpassword', methods=['GET', 'POST'])
def forgetpassword():
    if request.method == "POST":
        email = request.form["email"]
        
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM singup WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user:
            otp = str(random.randint(1000, 9999))
            session["otp"] = otp
            session["email"] = email

            if send_otp(email, otp):
                flash("OTP sent to your email.", "success")
                return redirect("/verifyotp")
            else:
                flash("Failed to send OTP. Try again.", "danger")
        else:
            flash("Email not registered!", "danger")
    
    return render_template("forgetpassword.html")

@app.route("/verifyotp", methods=["GET", "POST"])
def verifyotp():
    if request.method == "POST":
        otp1 = request.form.get("otp1")
        otp2 = request.form.get("otp2")
        otp3 = request.form.get("otp3")
        otp4 = request.form.get("otp4")
        
        if not (otp1 and otp2 and otp3 and otp4):
            flash("Please enter all OTP digits.", "danger")
            return redirect("/verifyotp")

        entered_otp = otp1 + otp2 + otp3 + otp4

        if "otp" in session and entered_otp == session["otp"]:
            flash("OTP Verified! Reset your password now.", "success")
            return redirect("/resetpassword")
        else:
            flash("Invalid OTP. Please try again.", "danger")
    
    return render_template("verifyotp.html")

@app.route("/resetpassword", methods=["GET", "POST"])
def resetpassword():
    if request.method == "POST":
        password = request.form["password"]
        confirmpassword = request.form["confirmpassword"]

        if password != confirmpassword:
            flash("Passwords do not match!", "danger")
            return redirect("/resetpassword")


        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("UPDATE singup SET password = %s, confirmpassword = %s", (password, confirmpassword))
        conn.commit()
        cursor.close()
        conn.close()

        session.pop("email", None)
        session.pop("otp", None)
        flash("Password reset successful! Login now.", "success")
        return redirect("/login")

    return render_template("resetpassword.html")



SIGNS_FOLDER = os.path.join(app.root_path, "static", "signs")


def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Jayesh@45",
        database="signease"
    )


def fetch_sign_images():
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("SELECT image_data, sign_name FROM sign_images")
    images = cursor.fetchall()
    db.close()
    return images


def convert_blob_to_image(blob_data):
    image_array = np.frombuffer(blob_data, dtype=np.uint8)
    img = cv2.imdecode(image_array, cv2.IMREAD_GRAYSCALE)
    return img if img is not None else None


def match_sign(uploaded_image):
    orb = cv2.ORB_create()
    uploaded_gray = cv2.cvtColor(uploaded_image, cv2.COLOR_BGR2GRAY)
    kp1, des1 = orb.detectAndCompute(uploaded_gray, None)
    
    if des1 is None or len(kp1) < 10:  
        return None

    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    best_match = None
    best_score = 0
    MATCH_THRESHOLD = 50  

    for blob, text in fetch_sign_images():
        db_image = convert_blob_to_image(blob)
        if db_image is None:
            continue
        
        kp2, des2 = orb.detectAndCompute(db_image, None)
        if des2 is None or len(kp2) < 10:
            continue
        
        matches = bf.match(des1, des2)
        score = len(matches)
        
        if score > best_score and score > MATCH_THRESHOLD:  
            best_score = score
            best_match = text
    
    return best_match if best_match else None

SIGNS_FOLDER = "static/signs"


@app.route('/converter')
def index():
    return render_template("converter.html")

def get_db_connection():
    """Establish a connection to MySQL Database using DB_CONFIG"""
    return mysql.connector.connect(**DB_CONFIG)


def get_sign_image(word):
    """Check if the word sign exists in the static folder or database (Supports .png & .jpeg)"""

    
    for ext in ["png", "jpeg"]:
        image_filename = f"{word}.{ext}"
        image_path = os.path.join(SIGNS_FOLDER, image_filename)
        if os.path.exists(image_path):
            return image_filename 

    
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("SELECT image_data FROM sign_images WHERE sign_name = %s", (word,))
    result = cursor.fetchone()
    db.close()

    return image_filename if result else None 

@app.route('/text-to-sign', methods=['POST'])
def text_to_sign():
    """Converts text to sign language images"""
    data = request.get_json()
    text = data.get("text", "").strip().lower()
    words = text.split()

    images = []

    for word in words:
        img = get_sign_image(word)
        if img:
            images.append(img) 
        else:
            
            for letter in word:
                letter_img = get_sign_image(letter)
                if letter_img:
                    images.append(letter_img)

    if images:
        return jsonify({"images": images}) 
    return jsonify({"error": "Sign not found"}), 404



def get_image_from_db(sign_name):
    """Fetches an image from a MySQL database as a NumPy array."""
    
   
    conn = mysql.connector.connect(
        host="localhost",        
        user="root",    
        password="Jayesh@45",
        database="signease" 
    )
    cursor = conn.cursor()

   
    cursor.execute("SELECT image_data FROM sign_images WHERE sign_name=%s", (sign_name,))
    result = cursor.fetchone() 

    conn.close()  

    if result is None:
        return None  

    
    image_array = np.frombuffer(result[0], np.uint8)
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

    return image

def compare_images(image1, image2):
    """ Compares two images and returns True if they are similar. """
    if image1 is None or image2 is None:
        return False 

    
    image1_gray = cv2.cvtColor(image1, cv2.COLOR_BGR2GRAY)
    image2_gray = cv2.cvtColor(image2, cv2.COLOR_BGR2GRAY)

    
    image2_gray = cv2.resize(image2_gray, (image1_gray.shape[1], image1_gray.shape[0]))

    
    similarity_score, _ = ssim(image1_gray, image2_gray, full=True)

    return similarity_score > 0.8  


@app.route('/signtotext', methods=['POST'])
def sign_to_text():
    """ Handles file uploads, processes images, and returns recognized sign names. """
    if 'files' not in request.files:
        return jsonify({"error": "No files provided"}), 400
    
    files = request.files.getlist('files')  
    recognized_texts = []

    for file in files:
        if file.filename == '':
            continue

        file_bytes = np.frombuffer(file.read(), np.uint8)
        uploaded_image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

        if uploaded_image is None:
            continue

        recognized_text = match_sign(uploaded_image)  

       
        clean_text = os.path.splitext(recognized_text)[0]  
        
        recognized_texts.append(clean_text)

    if not recognized_texts:
        return jsonify({"error": "No valid images processed"}), 400

    return jsonify({"text": " ".join(recognized_texts)})




@app.route('/gamemode')
def game():
    return render_template('gamemode.html')  

@app.route('/learn')
def learn():
    return render_template('learn.html') 

@app.route('/community')
def community():
    return render_template('community.html')

@app.route('/termsnconditions')
def termsnconditions():
    return render_template('termsnconditions.html')  


UPLOAD_FOLDER = 'static/profile_pics'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route('/profile_pics/<filename>')
def profile_pics(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if request.method == 'POST':
       
        name = request.form.get('name')
        contact = request.form.get('contact')
        email = request.form.get('email')
        member_since = request.form.get('member_since')
        dob = request.form.get('dob')
        alt_email = request.form.get('alt_email')
        
        
        profile_pic = request.files.get('profile_pics')
        profile_pic_filename = None
        profile_pic_blob = None
        
        if profile_pic:
            profile_pic_filename = secure_filename(f"{email}_profile.png")
            profile_pic_path = os.path.join(app.config['UPLOAD_FOLDER'], profile_pic_filename)
            profile_pic.save(profile_pic_path)  
            
            
            with open(profile_pic_path, 'rb') as file:
                profile_pic_blob = file.read()

        
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        
        cursor.execute("""
            INSERT INTO users (name, contact, email, member_since, dob, alt_email, profile_pics, profile_pic_blob) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (name, contact, email, member_since, dob, alt_email, profile_pic_filename, profile_pic_blob))

        conn.commit()
        cursor.close()
        conn.close()


        return redirect(url_for('dashboard_page'))

    return render_template('profile.html')


@app.route('/get-profile/<email>', methods=['GET'])
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


@app.route('/dashboard')
def dashboard_view():
    return render_template("dashboard.html")





if __name__ == '__main__':
    app.run(debug=True)
