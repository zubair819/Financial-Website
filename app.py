from flask import Flask, render_template, request, redirect, url_for, session
from pymongo import MongoClient
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import bcrypt
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')  # Retrieve secret key from environment variables

# MongoDB setup
client = MongoClient(os.getenv('MONGO_URI'))
db = client['Financial_Website']
users = db['signup']
financial_data = db['financial_data']

# Email configuration
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
SMTP_USERNAME = os.getenv('SMTP_USERNAME')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')

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
        
        if users.find_one({'email': email}):
            return "Email already registered!"
        
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        otp = str(random.randint(100000, 999999))
        session['signup_otp'] = otp
        session['signup_email'] = email
        session['signup_password'] = hashed_password.decode('utf-8')
        
        send_otp(email, otp)
        return redirect(url_for('verify_signup_otp'))
    
    return render_template('signup.html')

@app.route('/verify_signup_otp', methods=['GET', 'POST'])
def verify_signup_otp():
    if request.method == 'POST':
        user_otp = request.form['otp']
        if user_otp == session['signup_otp']:
            users.insert_one({
                'email': session['signup_email'],
                'password': session['signup_password']
            })
            return redirect(url_for('login'))
        else:
            return "Invalid OTP. Please try again."
    
    return render_template('verify_otp.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = users.find_one({'email': email})

        if user and bcrypt.checkpw(password.encode('utf-8'), user['password']):
            session['email'] = email
            return redirect(url_for('dashboard'))
        else:
            return "Invalid credentials!"
    return render_template('login.html')

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        user = users.find_one({'email': email})
        if user:
            otp = str(random.randint(100000, 999999))
            session['reset_otp'] = otp
            session['reset_email'] = email
            send_otp(email, otp)
            return redirect(url_for('verify_reset_otp'))
        else:
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
        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        users.update_one(
            {'email': session['reset_email']},
            {'$set': {'password': hashed_password}}
        )
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

        existing_data = financial_data.find_one({
            'user_email': session['email'],
            'date': date
        })
       
        if existing_data:
            financial_data.update_one(
                {'_id': existing_data['_id']},
                {'$set': {
                    'income': income,
                    'entertainment': entertainment,
                    'grocery': grocery,
                    'snacks': snacks,
                    'bills': bills,
                    'salaries': salaries,
                    'total_expenditure': total_expenditure
                }}
            )
        else:
            financial_data.insert_one({
                'user_email': session['email'],
                'date': date,
                'income': income,
                'entertainment': entertainment,
                'grocery': grocery,
                'snacks': snacks,
                'bills': bills,
                'salaries': salaries,
                'total_expenditure': total_expenditure
            })
       
        return redirect(url_for('view_financial_data_tables'))
   
    date = request.args.get('date')
    if date:
        existing_data = financial_data.find_one({
            'user_email': session['email'],
            'date': date
        })
        if existing_data:
            return render_template('add_financial_data.html', data=existing_data)

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
       
        data = financial_data.find({
            'user_email': session['email'],
            'date': {'$gte': start_date, '$lte': end_date}
        }).sort('date')
       
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
            dates.append(entry['date'])
            income = entry.get('income', 0)
            earnings.append(income)
           
            total_expenditure = sum(entry.get(key, 0) for key in expenditures.keys())
            profit = income - total_expenditure
            profits.append(profit)
            if profit < 0:
                loss_days += 1
            
            daily_exp = []
            for key in expenditures.keys():
                value = entry.get(key, 0)
                expenditures[key].append(value)
                daily_exp.append(value)
            daily_expenditures.append(daily_exp)

        dates = list(dates)
        earnings = list(earnings)
        profits = list(profits)
        daily_expenditures = [list(day) for day in daily_expenditures]
       
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

    user_data = financial_data.find({'user_email': session['email']}).sort('date', -1)

    return render_template('view_financial_data_tables.html', financial_data=user_data)

if __name__ == '__main__':
    pass
