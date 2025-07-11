import os
import mysql.connector

# MySQL Database Configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Jayesh@45',
    'database': 'signease'
}

# Folder where images are stored
IMAGE_FOLDER = "output_images"

# Connect to MySQL
conn = mysql.connector.connect(**DB_CONFIG)
cursor = conn.cursor()

# Loop through all images in the folder
for filename in os.listdir(IMAGE_FOLDER):
    file_path = os.path.join(IMAGE_FOLDER, filename)

    # Read image as binary (BLOB)
    with open(file_path, 'rb') as file:
        image_data = file.read()

    # Check if image already exists in the database
    cursor.execute("SELECT id FROM sign_images WHERE sign_name = %s", (filename,))
    existing_image = cursor.fetchone()

    if existing_image:
        print(f"⚠️ Image '{filename}' already exists in the database. Skipping...")
    else:
        # Insert new image into the database
        cursor.execute("INSERT INTO sign_images (sign_name, image_data) VALUES (%s, %s)", (filename, image_data))
        print(f"✅ Image '{filename}' stored in the database!")

# Commit & Close Connection
conn.commit()
cursor.close()
conn.close()

print("🚀 Image processing complete!")
