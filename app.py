from flask import Flask, render_template
from extensions import mysql
import os
from routes.auth_routes import auth_bp

app = Flask(__name__)

# Secret Key Configuration
app.secret_key = '123456789'  # Use a stronger secret key in production

# MySQL Configuration
app.config['MYSQL_HOST'] = '127.0.0.1'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'admin@555'  # Ensure this is correct for your setup
app.config['MYSQL_DB'] = 'user_database'

# Initialize MySQL with the app
mysql.init_app(app)

# File upload folder configuration
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Ensure the upload folder exists

# Register blueprints
app.register_blueprint(auth_bp)

# Home route
@app.route('/')
def home():
    return render_template('index.html')  # Render the index.html file

if __name__ == '__main__':
    app.run(debug=True)
