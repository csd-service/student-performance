from flask import Flask, render_template
from flask_mysqldb import MySQL
import os
from routes.auth_routes import auth_bp, init_mysql  # Import the blueprint and setup function

app = Flask(__name__)

app.secret_key = os.urandom(24)

# Configure upload folder
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create uploads directory if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# MySQL Configuration
app.config['MYSQL_HOST'] = '127.0.0.1'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'admin@555'
app.config['MYSQL_DB'] = 'user_database'

mysql = MySQL(app)

# Pass MySQL instance to the blueprint
init_mysql(mysql)

# Register Blueprint
app.register_blueprint(auth_bp)

# Main route
@app.route('/')
def home():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
