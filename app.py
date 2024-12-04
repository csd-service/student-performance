from flask import Flask, render_template
from extensions import mysql
from routes.auth_routes import auth_bp

app = Flask(__name__)

# Secret Key Configuration
app.secret_key = '123456789'  

# MySQL Configuration
app.config['MYSQL_HOST'] = '127.0.0.1'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'admin@555'
app.config['MYSQL_DB'] = 'user_database'

# Initialize MySQL with the app
mysql.init_app(app)

# Register blueprints
app.register_blueprint(auth_bp)

@app.route('/')
def home():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
