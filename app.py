
from flask import Flask, render_template, request, redirect, url_for, session, make_response
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, Admin, SustainabilityData
import joblib
import numpy as np
from xhtml2pdf import pisa
from io import BytesIO
from sqlalchemy import func
import random

# === App Configuration ===
app = Flask(__name__)
app.secret_key = 'supersecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///eco.db'
db.init_app(app)

# === Load Trained AI Model ===
model = joblib.load("green_score_model.pkl")

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = Admin.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            session['username'] = user.username
            session['floor'] = user.floor
            return redirect(url_for('dashboard'))
        else:
            return "❌ Invalid credentials"
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        floor = request.form['floor']

        if password != confirm_password:
            return "❌ Passwords do not match. Please try again."

        existing_user = Admin.query.filter_by(username=username).first()
        if existing_user:
            return "❌ Username already exists."

        hashed_pw = generate_password_hash(password)
        new_admin = Admin(username=username, password=hashed_pw, floor=floor)
        db.session.add(new_admin)
        db.session.commit()

        return redirect(url_for('login'))

    return render_template("register.html")

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))

    floor = session['floor']
    user_data = SustainabilityData.query.filter_by(floor=floor).all()

    energy_data = [d.energy for d in user_data]
    water_data = [d.water for d in user_data]
    heat_data = [d.heat for d in user_data]
    waste_data = [d.waste for d in user_data]
    labels = list(range(1, len(energy_data) + 1))

    return render_template(
        'dashboard.html',
        user=session['username'],
        floor=floor,
        energy_data=energy_data,
        water_data=water_data,
        heat_data=heat_data,
        waste_data=waste_data,
        labels=labels
    )

@app.route('/submit-data', methods=['GET', 'POST'])
def submit_data():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        energy = float(request.form['energy'])
        water = float(request.form['water'])
        heat = float(request.form['heat'])
        waste = float(request.form['waste'])

        data = SustainabilityData(
            username=session['username'],
            floor=session['floor'],
            energy=energy,
            water=water,
            heat=heat,
            waste=waste
        )
        db.session.add(data)
        db.session.commit()

        features = np.array([[energy, water, heat, waste]])
        score = model.predict(features)[0]

        feedback = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Success</title>
    <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: 'Segoe UI', sans-serif;
            background: url('/static/bg_submit.jpg') no-repeat center center fixed;
            background-size: cover;
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100vh;
        }}
        .card {{
            background-color: rgba(0, 0, 0, 0.8);
            padding: 40px;
            border-radius: 15px;
            text-align: center;
            width: 600px;
            box-shadow: 0 0 25px #00ffcc;
        }}
        .tick {{
            width: 100px;
            margin-bottom: 20px;
        }}
        h2 {{
            font-size: 28px;
            margin-bottom: 10px;
            color: #00ffcc;
        }}
        p {{
            font-size: 18px;
        }}
        .warning {{
            color: gold;
            margin-top: 10px;
        }}
        a {{
            display: inline-block;
            margin-top: 20px;
            color: #00ffcc;
            font-weight: bold;
            text-decoration: none;
            font-size: 16px;
        }}
    </style>
</head>
<body>
    <div class="card">
        <img src='/static/success.gif' alt='Success' class='tick'>
        <h2>✅ Data Submitted Successfully!</h2>
        <p><strong>🌿 Green Score:</strong> {round(score, 2)}</p>
"""
        if score < 50:
            feedback += "<p class='warning'>⚠️ Low Green Score. Try reducing power or water usage.</p>"
        if heat > 30:
            feedback += "<p class='warning'>🔥 High heat detected. Consider reducing appliance use.</p>"
        if waste > 5:
            feedback += "<p class='warning'>🗑️ High waste generated. Try composting or better sorting.</p>"

        feedback += """<br><a href='/dashboard'>⬅️ Back to Dashboard</a>
    </div>
</body>
</html>
"""
        return feedback

    return render_template('submit_data.html')

@app.route('/leaderboard')
def leaderboard():
    scores = db.session.query(
        SustainabilityData.floor,
        func.avg(SustainabilityData.energy).label('avg_energy'),
        func.avg(SustainabilityData.water).label('avg_water'),
        func.avg(SustainabilityData.heat).label('avg_heat'),
        func.avg(SustainabilityData.waste).label('avg_waste')
    ).group_by(SustainabilityData.floor).all()

    leaderboard_data = []
    for row in scores:
        # Calculate green score using the weighted formula
        score = round(
            row.avg_energy * -0.3 +
            row.avg_water * -0.2 +
            row.avg_heat * -0.1 +
            row.avg_waste * -0.4,
            2
        )
        leaderboard_data.append({
            'floor': row.floor,
            'score': score
        })

    # Sort by score descending
    leaderboard_data = sorted(leaderboard_data, key=lambda x: x['score'], reverse=True)

    return render_template("leaderboard.html", scores=leaderboard_data)


@app.route('/report')
def generate_report():
    floor = session.get('floor')
    user_data = SustainabilityData.query.filter_by(floor=floor).all()
    html = render_template("report_template.html", data=user_data, floor=floor)
    result = BytesIO()
    pisa.CreatePDF(html, dest=result)
    response = make_response(result.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=EcoReport.pdf'
    return response

@app.route('/eco-tips')
def eco_tips():
    tips = [
        "💡 Turn off lights when not needed",
        "🚿 Fix leaky taps to save water",
        "♻️ Separate your waste properly",
        "🌞 Use natural light during daytime",
        "🪟 Improve ventilation instead of using AC"
    ]
    return render_template("eco_tips.html", tip=random.choice(tips))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))



@app.route('/about')
def about():
    return render_template('about.html')

if __name__ == '__main__':
    app.run(debug=True)
