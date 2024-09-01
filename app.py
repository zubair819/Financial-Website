from flask import Flask, render_template, request, redirect, url_for, session
from mysql.connector import connect, Error
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import bcrypt
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Set a secret key for session management

# MySQL configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'zubair084',
    'database': 'financial_website'
}

# Email configuration
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
SMTP_USERNAME = '944829zubair@gmail.com'
SMTP_PASSWORD = 'ruar tyto evdl yjfx'

def get_db_connection():
    return connect(**DB_CONFIG)

def send_otp(email, otp):
    message = MIMEMultipart()
    message['From'] = SMTP_USERNAME
    message['To'] = email
    message['Subject'] = 'Your OTP for verification'
    body = f'Your OTP is: {otp}'
    message.attach(MIMEText(body, 'plain'))

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(message)

@app.route('/')
def dashboard():
    return render_template('index.html')

@app.route('/logout')
def logout():
    session.pop('email', None)
    return redirect(url_for('dashboard'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return "Email already registered!"
        
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        otp = str(random.randint(100000, 999999))
        session['signup_otp'] = otp
        session['signup_email'] = email
        session['signup_password'] = hashed_password
        
        send_otp(email, otp)
        
        cursor.close()
        conn.close()
        
        return redirect(url_for('verify_signup_otp'))
    
    return render_template('signup.html')

@app.route('/verify_signup_otp', methods=['GET', 'POST'])
def verify_signup_otp():
    if request.method == 'POST':
        user_otp = request.form['otp']
        if user_otp == session['signup_otp']:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("INSERT INTO users (email, password) VALUES (%s, %s)",
                           (session['signup_email'], session['signup_password']))
            conn.commit()
            
            cursor.close()
            conn.close()
            
            return redirect(url_for('login'))
        else:
            return "Invalid OTP. Please try again."
    
    return render_template('verify_otp.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        
        if user and bcrypt.checkpw(password.encode('utf-8'), user[2].encode('utf-8')):
            session['email'] = email
            cursor.close()
            conn.close()
            return render_template('index.html')
        else:
            cursor.close()
            conn.close()
            return "Invalid credentials!"
    
    return render_template('login.html')

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        
        if user:
            otp = str(random.randint(100000, 999999))
            session['reset_otp'] = otp
            session['reset_email'] = email
            send_otp(email, otp)
            
            cursor.close()
            conn.close()
            
            return redirect(url_for('verify_reset_otp'))
        else:
            cursor.close()
            conn.close()
            return "Email not found!"
    
    return render_template('forgot_password.html')

@app.route('/verify_reset_otp', methods=['GET', 'POST'])
def verify_reset_otp():
    if request.method == 'POST':
        user_otp = request.form['otp']
        if user_otp == session['reset_otp']:
            return redirect(url_for('reset_password'))
        else:
            return "Invalid OTP. Please try again."
    return render_template('verify_otp.html')

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        new_password = request.form['new_password']
        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("UPDATE users SET password = %s WHERE email = %s",
                       (hashed_password, session['reset_email']))
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return redirect(url_for('login'))
    
    return render_template('reset_password.html')

@app.route('/add_financial_data', methods=['GET', 'POST'])
def add_financial_data():
    if 'email' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        date = request.form['date']
        income = float(request.form['income'])
        entertainment = float(request.form.get('entertainment', 0))
        grocery = float(request.form.get('grocery', 0))
        snacks = float(request.form.get('snacks', 0))
        bills = float(request.form.get('bills', 0))
        salaries = float(request.form.get('salaries', 0))
        
        total_expenditure = entertainment + grocery + snacks + bills + salaries

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM users WHERE email = %s", (session['email'],))
        user_id = cursor.fetchone()[0]

        cursor.execute("""
            INSERT INTO financial_data 
            (user_id, date, income, entertainment, grocery, snacks, bills, salaries, total_expenditure)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            income = VALUES(income),
            entertainment = VALUES(entertainment),
            grocery = VALUES(grocery),
            snacks = VALUES(snacks),
            bills = VALUES(bills),
            salaries = VALUES(salaries),
            total_expenditure = VALUES(total_expenditure)
        """, (user_id, date, income, entertainment, grocery, snacks, bills, salaries, total_expenditure))
        
        conn.commit()
        cursor.close()
        conn.close()

        return redirect(url_for('view_financial_data_tables'))
   
    today = datetime.now()
    one_month_ago = today - timedelta(days=30)
    return render_template('add_financial_data.html', min_date=one_month_ago.date(), max_date=today.date())

@app.route('/view_financial_data', methods=['GET', 'POST'])
def view_financial_data():
    if 'email' not in session:
        return redirect(url_for('login'))
   
    if request.method == 'POST':
        start_date = request.form['start_date']
        end_date = request.form['end_date']
       
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT id FROM users WHERE email = %s", (session['email'],))
        user_id = cursor.fetchone()['id']

        cursor.execute("""
            SELECT * FROM financial_data
            WHERE user_id = %s AND date BETWEEN %s AND %s
            ORDER BY date
        """, (user_id, start_date, end_date))
        
        data = cursor.fetchall()
        
        cursor.close()
        conn.close()

        dates = []
        earnings = []
        expenditures = {
            'entertainment': [],
            'grocery': [],
            'snacks': [],
            'bills': [],
            'salaries': []
        }
        profits = []
        loss_days = 0
        daily_expenditures = []

        for entry in data:
            dates.append(entry['date'].strftime('%Y-%m-%d'))
            income = entry['income']
            earnings.append(income)
           
            total_expenditure = entry['total_expenditure']
            profit = income - total_expenditure
            profits.append(profit)
            if profit < 0:
                loss_days += 1
            
            daily_exp = []
            for key in expenditures.keys():
                value = entry[key]
                expenditures[key].append(value)
                daily_exp.append(value)
            daily_expenditures.append(daily_exp)

        return render_template(
            'financial_graphs.html',
            dates=dates,
            earnings=earnings,
            expenditures=expenditures,
            profits=profits,
            loss_days=loss_days,
            daily_expenditures=daily_expenditures
        )
   
    return render_template('view_financial_data.html')

@app.route('/view_financial_data_tables')
def view_financial_data_tables():
    if 'email' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT id FROM users WHERE email = %s", (session['email'],))
    user_id = cursor.fetchone()['id']

    cursor.execute("""
        SELECT * FROM financial_data
        WHERE user_id = %s
        ORDER BY date DESC
    """, (user_id,))
    
    financial_data = cursor.fetchall()
    
    cursor.close()
    conn.close()

    return render_template('view_financial_data_tables.html', financial_data=financial_data)

if __name__ == '__main__':
    app.run(debug=True)