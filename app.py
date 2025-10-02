from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import os, csv, json, subprocess, secrets
from datetime import datetime
import pandas as pd
from collections import Counter

app = Flask(__name__)
app.secret_key = 'MINDCARE'

# --- CONFIG ---
app.static_folder = 'static'
app.template_folder = 'templates'

LANGUAGES = {'en': 'English', 'hi': 'Hindi', 'ks': 'Kashmiri'}

DUMMY_USERS = {'student1': {'password': 'password123'}}
COUNSELORS = {'dr.reid': 'psychology101', 'ms.garcia': 'wellnesspass'}

APPOINTMENTS = [
    {'student_name': 'Alex Johnson', 'date': '2025-09-18', 'time': '10:00 AM', 'notes': 'Anxiety over exams.'},
    {'student_name': 'Brenda Smith', 'date': '2025-09-18', 'time': '11:30 AM', 'notes': 'Career path discussion.'},
    {'student_name': 'Charles Davis', 'date': '2025-09-19', 'time': '02:00 PM', 'notes': 'Follow-up session.'},
    {'student_name': 'Diana Miller', 'date': '2025-09-20', 'time': '09:00 AM', 'notes': 'Initial consultation.'},
]

AVAILABLE_SLOTS = [
    "09:00 - 10:00", "10:00 - 11:00", "11:00 - 12:00", "12:00 - 13:00",
    "14:00 - 15:00", "15:00 - 16:00", "16:00 - 17:00", "17:00 - 18:00"
]

CSV_FILE = 'JnKDataset.csv'

# --- HELPER FUNCTIONS ---
def generate_new_student_id():
    if not os.path.exists(CSV_FILE):
        return "STU001"
    try:
        df = pd.read_csv(CSV_FILE)
        if df.empty:
            return "STU001"
        last_id = df['student_id'].iloc[-1]
        last_num = int(last_id.replace('STU', ''))
        new_num = last_num + 1
        return f"STU{new_num:03d}"
    except (pd.errors.EmptyDataError, IndexError, FileNotFoundError, ValueError):
        return "STU001"

def get_phq_category(score):
    if score <= 4: return "Minimal"
    if score <= 9: return "Mild"
    if score <= 14: return "Moderate"
    if score <= 19: return "Moderately Severe"
    return "Severe"

def get_gad_category(score):
    if score <= 4: return "Minimal"
    if score <= 9: return "Mild"
    if score <= 14: return "Moderate"
    return "Severe"

def get_ghq_category(score):
    if score <= 4: return "Minimal"
    if score <= 8: return "Mild"
    return "Moderate"

def get_composite_risk(total_score):
    if total_score < 20: return "Low Risk"
    if total_score <= 40: return "Moderate Risk"
    return "High Risk"

# --- CHATBOT HELPER ---
def run_ollama(system_prompt, user_message):
    cmd = [
        "ollama", "run", "gemma3:1b",
        f"System: {system_prompt}\nUser: {user_message}\nAssistant:"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout.strip()

# --- ROUTES ---

# Home & Multi-language
@app.route('/')
def home(): return render_template('index.html')
@app.route('/index_<lang>') 
def home_lang(lang): 
    return render_template(f'index_{lang}.html') if lang in LANGUAGES else redirect(url_for('home'))

# Resources
@app.route('/resources')
def resources(): return render_template('resources.html')
@app.route('/resources_<lang>')
def resources_lang(lang):
    return render_template(f'resources_{lang}.html') if lang in LANGUAGES else redirect(url_for('resources'))

# Support
@app.route('/support')
def support(): return render_template('support.html')
@app.route('/support_<lang>')
def support_lang(lang):
    return render_template(f'support_{lang}.html') if lang in LANGUAGES else redirect(url_for('support'))

# --- CHATBOT INTEGRATION ---
@app.route('/chat-support')
def chat_support(): 
    return render_template('chat-support.html')

@app.route('/chat-support_<lang>')
def chat_support_lang(lang):
    return render_template(f'chat-support_{lang}.html') if lang in LANGUAGES else redirect(url_for('chat_support'))

# --- CHATBOT API ---
@app.route("/chat", methods=["POST"])
def chat_api():
    user_message = request.json.get("message", "").strip()
    selected_lang = request.json.get("lang", "en")  # Language sent from frontend

    if not user_message:
        # Default greeting per language
        greetings = {
            "en": "Hello! I'm your MindCare assistant. How are you feeling today?",
            "hi": "नमस्ते! मैं आपका MindCare सहायक हूँ। आप आज कैसा महसूस कर रहे हैं?",
            "ks": "سلام! میں آپ کا MindCare معاون ہوں۔ آج آپ کیسا محسوس کر رہے ہیں؟"
        }
        return jsonify({"response": greetings.get(selected_lang, greetings["en"])})

    # Map frontend codes to language names
    lang_map = {"en": "English", "hi": "Hindi", "ks": "Kashmiri"}
    chosen_lang = lang_map.get(selected_lang, "English")

    system_prompt = f"""
You are an AI mental health chatbot with the ability to converse in English, Hindi, and Urdu. You are an AI assistant, not a human, therapist, doctor, or medical professional.
Your primary role is to provide short, warm, and conversational responses, always in the language chosen by the user. 
The user has chosen to speak in {chosen_lang}.
RULES (You must follow these):
1. Reflect: Begin by reflecting the user's expressed feeling in one short sentence.
2. Suggest (Optional): If appropriate, offer a single, simple coping suggestion in one short sentence.
3. Inquire: Always end your response with a gentle, open-ended question to encourage the user to continue sharing.
4. Boundaries: NEVER provide medical or diagnostic advice. If a user asks about medication or methods of self-harm, state your limitations briefly and transparently.
5. Crisis Protocol: If the user expresses intent for suicide or self-harm or to harm someone else, your response must be exactly this:
Deliver two short sentences expressing compassion and stating your limitations as an AI.
Immediately provide these helpline numbers(don't ask,straight away provide it): 14416, 1-800-891-4416, 1800-180-7020, 8448-8448-45.
End by asking if they can call one of these numbers or get help now.
Tone: Your tone must always be calm, compassionate, and concise.
Length: Keep your standard replies brief, around 30–50 words.
Example Training Dialogues (Internal examples for your understanding, DO NOT display these to the user):
* English
    * USER: English
    * ASSISTANT: How are you feeling today?
    * USER: I'm so stressed about my exams.
    * ASSISTANT: That sounds really heavy, like it’s hard to focus. Maybe a short break with deep breathing could help. What’s the toughest part for you right now?
* Hindi (हिंदी)
    * USER: हिंदी
    * ASSISTANT: आज आप कैसा महसूस कर रहे हैं?
    * USER: मैं बहुत परेशान हूँ, नींद नहीं आ रही।
    * ASSISTANT: यह सच में थकाने वाला लगता है। हल्की साँस लेने की कसरत मदद कर सकती है: चार सेकंड तक गहरी साँस लें, फिर चार सेकंड में छोड़ें। क्या आप इसे अभी आज़माना चाहेंगे?
* Urdu (اُردُو)
    * USER: اُردُو
    * ASSISTANT: آپ آج کیسا محسوس کر رہے ہیں؟
    * USER: میں بہت پریشان ہوں اور نیند نہیں آتی۔
    * ASSISTANT: یہ واقعی تھکا دینے والا لگتا ہے۔ ایک چھوٹی سی سانس لینے کی مشق مدد کر سکتی ہے: چار سیکنڈ سانس لیں، چار سیکنڈ چھوڑیں۔ کیا آپ ابھی یہ آزمائیں گے؟

Reply in {chosen_lang}.
"""

    try:
        response = run_ollama(system_prompt, user_message)
        return jsonify({"response": response})
    except Exception as e:
        return jsonify({"response": f"⚠️ Error: {str(e)}"})

    
@app.route("/reset")
def reset():
    session.clear()
    return jsonify({
        "response": "Language reset. Which language would you like to talk in? (English / हिंदी / اُردُو)"
    })


# --- AUTHENTICATION AND BOOKING ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'username' in session: return redirect(url_for('booking'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = DUMMY_USERS.get(username)
        if user and user.get('password') == password:
            session['username'] = username
            flash('Login successful!', 'success')
            return redirect(url_for('booking'))
        else: flash('Invalid username or password.', 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in DUMMY_USERS:
            flash('Username already exists.', 'error')
            return redirect(url_for('register'))
        session['registration_data'] = {
            'username': username,
            'password': password,
            'district': request.form.get('district'),
            'college_name': request.form.get('college_name'),
            'course': request.form.get('course'),
            'year_of_study': request.form.get('year_of_study'),
            'gender': request.form.get('gender'),
            'age_group': request.form.get('age_group')
        }
        DUMMY_USERS[username] = {'password': password}
        session['username'] = username
        flash('Registration successful! Please complete the questionnaire.', 'success')
        return redirect(url_for('questionnaire'))
    return render_template('register.html')

@app.route('/questionnaire', methods=['GET', 'POST'])
def questionnaire():
    if 'username' not in session: return redirect(url_for('login'))

    questions_data = {
        "Depression (PHQ-9)": [("phq1", "Little interest or pleasure in doing things"),
                               ("phq2", "Feeling down, depressed, or hopeless"),
                               ("phq3", "Trouble falling/staying asleep, or sleeping too much"),
                               ("phq4", "Feeling tired or having little energy"),
                               ("phq5", "Poor appetite or overeating"),
                               ("phq6", "Feeling bad about yourself — or that you are a failure or have let yourself/your family down"),
                               ("phq7", "Trouble concentrating on things, such as reading or watching TV"),
                               ("phq8", "Moving/speaking so slowly that others noticed, or being fidgety/restless"),
                               ("phq9", "Thoughts that you would be better off dead, or of hurting yourself")],
        "Anxiety (GAD-7)": [("gad1", "Feeling nervous, anxious, or on edge"),
                             ("gad2", "Not being able to stop or control worrying"),
                             ("gad3", "Worrying too much about different things"),
                             ("gad4", "Trouble relaxing"),
                             ("gad5", "Being so restless that it’s hard to sit still"),
                             ("gad6", "Becoming easily annoyed or irritable"),
                             ("gad7", "Feeling afraid as if something awful might happen")],
        "General Mental Health (GHQ Selected)": [("ghq1", "Lost much sleep over worry?"),
                                                 ("ghq2", "Been able to concentrate on what you are doing?"),
                                                 ("ghq3", "Been thinking of yourself as a worthless person?"),
                                                 ("ghq4", "Been feeling reasonably happy, considering all the circumstances?")]
    }
    options_data = {"0": "Not at all", "1": "Several days", "2": "> Half the days", "3": "Nearly every day"}

    if request.method == 'POST':
        reg_data = session.pop('registration_data', {})
        if not reg_data:
            flash('Registration data not found. Please register again.', 'error')
            return redirect(url_for('register'))

        phq_answers = [int(request.form.get(f'phq{i}', 0)) for i in range(1, 10)]
        gad_answers = [int(request.form.get(f'gad{i}', 0)) for i in range(1, 8)]
        ghq_answers = [int(request.form.get(f'ghq{i}', 0)) for i in range(1, 5)]

        phq_score = sum(phq_answers)
        gad_score = sum(gad_answers)
        ghq_score = sum(ghq_answers)
        total_score = phq_score + gad_score + ghq_score

        new_row = {
            'student_id': generate_new_student_id(),
            'district': reg_data.get('district'), 'college_name': reg_data.get('college_name'),
            'course': reg_data.get('course'), 'year_of_study': reg_data.get('year_of_study'),
            'gender': reg_data.get('gender'), 'age_group': reg_data.get('age_group'),
            **{f'Q{i+1}': ans for i, ans in enumerate(phq_answers + gad_answers + ghq_answers)},
            'PHQ_score': phq_score, 'PHQ_category': get_phq_category(phq_score),
            'GAD_score': gad_score, 'GAD_category': get_gad_category(gad_score),
            'GHQ_score': ghq_score, 'GHQ_category': get_ghq_category(ghq_score),
            'Composite_Score': total_score, 'Risk_Level': get_composite_risk(total_score),
            'Timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        if not os.path.exists(CSV_FILE):
            pd.DataFrame([new_row]).to_csv(CSV_FILE, index=False)
        else:
            df = pd.read_csv(CSV_FILE)
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            df.to_csv(CSV_FILE, index=False)

        flash('Questionnaire submitted successfully!', 'success')
        return redirect(url_for('booking'))

    return render_template('questionnaire.html', questions=questions_data, options=options_data)

# Booking
@app.route('/booking', methods=['GET', 'POST'])
def booking():
    if 'username' not in session: return redirect(url_for('login'))

    if request.method == 'POST':
        selected_slot = request.form.get('slot')
        student_name = session['username']
        for appt in APPOINTMENTS:
            if appt['student_name'] == student_name:
                appt['time'] = selected_slot
                flash('Slot updated successfully!', 'success')
                return redirect(url_for('booking'))
        APPOINTMENTS.append({'student_name': student_name, 'date': datetime.now().strftime('%Y-%m-%d'), 'time': selected_slot, 'notes': ''})
        flash('Slot booked successfully!', 'success')
        return redirect(url_for('booking'))

    student_name = session['username']
    student_appt = next((a for a in APPOINTMENTS if a['student_name'] == student_name), None)
    return render_template('booking.html', appointments=APPOINTMENTS, slots=AVAILABLE_SLOTS, student_appointment=student_appt)

# Counselor login
@app.route('/counselor-login', methods=['GET', 'POST'])
def counselor_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in COUNSELORS and COUNSELORS[username] == password:
            session['counselor'] = username
            flash('Counselor login successful!', 'success')
            return redirect(url_for('view_appointments'))
        flash('Invalid credentials.', 'error')
    return render_template('counselor_login.html')

@app.route('/view-appointments')
def view_appointments():
    if 'counselor' not in session: return redirect(url_for('counselor_login'))
    return render_template('view_appointments.html', appointments=APPOINTMENTS)

# Logout
@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('home'))

# Run app
if __name__ == '__main__':
    app.run(debug=True)
