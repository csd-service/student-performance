from flask import Flask, render_template
from flask_mysqldb import MySQL
from flask_bcrypt import Bcrypt
import os
from routes.auth_routes import auth_bp, init_mysql, init_bcrypt  # Added init_bcrypt

app = Flask(__name__)
bcrypt = Bcrypt(app)  # Initialize Bcrypt

app.secret_key = os.urandom(24)

# Configure upload folder
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# MySQL Configuration
app.config['MYSQL_HOST'] = '127.0.0.1'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'admin@555'
app.config['MYSQL_DB'] = 'user_database'

mysql = MySQL(app)

# Pass MySQL and Bcrypt instances to the blueprint
init_mysql(mysql)
init_bcrypt(bcrypt)

# Register Blueprint
app.register_blueprint(auth_bp)

@app.route('/')
def home():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)