from flask import Flask, render_template, request, redirect, url_for, flash, session
import os
from datetime import datetime
import pandas as pd

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'

# Configure static and template folders
app.static_folder = 'static'
app.template_folder = 'templates'

# Supported languages
LANGUAGES = {
    'en': 'English',
    'hi': 'Hindi',
    'ks': 'Kashmiri'
}

@app.route('/')
def home():
    # Default to English homepage; use /index_<lang> for other languages
    return render_template('index.html')

@app.route('/index_<lang>')
def home_lang(lang):
    if lang in LANGUAGES:
        return render_template(f'index_{lang}.html')
    return redirect(url_for('home'))

@app.route('/resources')
def resources():
    return render_template('resources.html')

@app.route('/resources_<lang>')
def resources_lang(lang):
    if lang in LANGUAGES:
        return render_template(f'resources_{lang}.html')
    return redirect(url_for('resources'))

@app.route('/support')
def support():
    return render_template('support.html')

@app.route('/support_<lang>')
def support_lang(lang):
    if lang in LANGUAGES:
        return render_template(f'support_{lang}.html')
    return redirect(url_for('support'))

@app.route('/chat-support')
def chat_support():
    return render_template('chat-support.html')

@app.route('/chat-support_<lang>')
def chat_support_lang(lang):
    if lang in LANGUAGES:
        return render_template(f'chat-support_{lang}.html')
    return redirect(url_for('chat_support'))

# API endpoints for chat functionality
@app.route('/api/chat', methods=['POST'])
def chat_api():
    """Handle chat messages from the AI support system"""
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        
        # This is where you would integrate your actual AI/chatbot
        # For now, returning a simple response
        bot_response = f"I understand you're saying: '{user_message}'. As an AI assistant, I'm here to listen and provide support. If you're in crisis, please reach out to a human counselor or emergency services."
        
        return {
            'response': bot_response,
            'status': 'success'
        }
    except Exception as e:
        return {
            'response': 'I apologize, but I encountered an error. Please try again or contact support.',
            'status': 'error'
        }, 500

@app.route('/api/book-session', methods=['POST'])
def book_session():
    """Handle session booking requests"""
    try:
        data = request.get_json()
        
        # Extract booking data
        name = data.get('name')
        email = data.get('email')
        date = data.get('date')
        time = data.get('time')
        issue_type = data.get('issue_type')
        
        # Here you would typically save to a database
        # For now, just return success
        
        return {
            'message': 'Session booked successfully! You will receive a confirmation email shortly.',
            'status': 'success'
        }
    except Exception as e:
        return {
            'message': 'There was an error booking your session. Please try again.',
            'status': 'error'
        }, 500

@app.route('/api/forum-post', methods=['POST'])
def create_forum_post():
    """Handle new forum post creation"""
    try:
        data = request.get_json()
        
        title = data.get('title')
        category = data.get('category')
        content = data.get('content')
        
        # Here you would save to database
        # For now, just return success
        
        return {
            'message': 'Post created successfully!',
            'status': 'success'
        }
    except Exception as e:
        return {
            'message': 'There was an error creating your post. Please try again.',
            'status': 'error'
        }, 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

# Ensure the CSV file path is correct
CSV_FILE = 'JnKDataset.csv'

# This is still used for quick login checks.
DUMMY_USERS = {
    'student1': {'password': 'password123'}
}

AVAILABLE_SLOTS = [
    "09:00 - 10:00", "10:00 - 11:00", "11:00 - 12:00", "12:00 - 13:00",
    "14:00 - 15:00", "15:00 - 16:00", "16:00 - 17:00", "17:00 - 18:00"
]

# --- HELPER FUNCTIONS ---
def generate_new_student_id():
    """Generates a new student ID by incrementing the last one in the CSV."""
    print(f"DEBUG: Checking for CSV file at: {os.path.abspath(CSV_FILE)}")
    if not os.path.exists(CSV_FILE):
        print("DEBUG: CSV file not found. Starting with STU001.")
        return "STU001"
    try:
        df = pd.read_csv(CSV_FILE)
        if df.empty:
            print("DEBUG: CSV is empty. Starting with STU001.")
            return "STU001"
        last_id = df['student_id'].iloc[-1]
        last_num = int(last_id.replace('STU', ''))
        new_num = last_num + 1
        new_id = f"STU{new_num:03d}"
        print(f"DEBUG: Last ID was {last_id}. New ID is {new_id}.")
        return new_id
    except (pd.errors.EmptyDataError, IndexError, FileNotFoundError, ValueError) as e:
        print(f"DEBUG: Error reading CSV for ID generation: {e}. Defaulting to STU001.")
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

# --- ROUTES ---
@app.route('/')
def landing_page():
    return render_template('landing.html')

@app.route('/login', methods=['GET', 'POST'])
# ... (login route is unchanged)
def login():
    if 'username' in session:
        return redirect(url_for('booking'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = DUMMY_USERS.get(username)
        if user and user.get('password') == password:
            session['username'] = username
            flash('Login successful!', 'success')
            return redirect(url_for('booking'))
        else:
            flash('Invalid username or password.', 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
# ... (register route is unchanged)
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in DUMMY_USERS:
            flash('Username already exists. Please choose another.', 'error')
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
    if 'username' not in session:
        return redirect(url_for('login'))

    questions_data = {
        "Depression (PHQ-9)": [
            ("phq1", "Little interest or pleasure in doing things"), ("phq2", "Feeling down, depressed, or hopeless"),
            ("phq3", "Trouble falling/staying asleep, or sleeping too much"), ("phq4", "Feeling tired or having little energy"),
            ("phq5", "Poor appetite or overeating"), ("phq6", "Feeling bad about yourself — or that you are a failure or have let yourself/your family down"),
            ("phq7", "Trouble concentrating on things, such as reading or watching TV"), ("phq8", "Moving/speaking so slowly that others noticed, or being fidgety/restless"),
            ("phq9", "Thoughts that you would be better off dead, or of hurting yourself"),
        ],
        "Anxiety (GAD-7)": [
            ("gad1", "Feeling nervous, anxious, or on edge"), ("gad2", "Not being able to stop or control worrying"),
            ("gad3", "Worrying too much about different things"), ("gad4", "Trouble relaxing"),
            ("gad5", "Being so restless that it’s hard to sit still"), ("gad6", "Becoming easily annoyed or irritable"),
            ("gad7", "Feeling afraid as if something awful might happen"),
        ],
        "General Mental Health (GHQ Selected)": [
            ("ghq1", "Lost much sleep over worry?"), ("ghq2", "Been able to concentrate on what you are doing?"),
            ("ghq3", "Been thinking of yourself as a worthless person?"), ("ghq4", "Been feeling reasonably happy, considering all the circumstances?"),
        ]
    }
    
    options_data = {"0": "Not at all", "1": "Several days", "2": "> Half the days", "3": "Nearly every day"}
    
    if request.method == 'POST':
        reg_data = session.pop('registration_data', None)
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
            'district': reg_data['district'], 'college_name': reg_data['college_name'], 'course': reg_data['course'],
            'year_of_study': reg_data['year_of_study'], 'gender': reg_data['gender'], 'age_group': reg_data['age_group'],
            **{f'Q{i+1}': ans for i, ans in enumerate(phq_answers + gad_answers + ghq_answers)},
            'PHQ_score': phq_score, 'PHQ_category': get_phq_category(phq_score),
            'GAD_score': gad_score, 'GAD_category': get_gad_category(gad_score),
            'GHQ_score': ghq_score, 'GHQ_category': get_ghq_category(ghq_score),
            'total_score': total_score, 'composite_risk': get_composite_risk(total_score)
        }
        
        try:
            new_df = pd.DataFrame([new_row])
            file_exists = os.path.exists(CSV_FILE)
            print(f"DEBUG: Appending to CSV. File exists: {file_exists}")
            # Ensure all columns from the original CSV are present, to prevent errors
            # This is a robust way to handle potentially missing columns
            if file_exists:
                original_df = pd.read_csv(CSV_FILE)
                new_df = pd.concat([original_df, new_df], ignore_index=True)
                new_df.to_csv(CSV_FILE, index=False)
            else:
                 new_df.to_csv(CSV_FILE, index=False, header=True)

            print("DEBUG: Successfully appended data to CSV.")
            flash('Thank you! Your information has been saved.', 'success')
            return redirect(url_for('booking'))
        except Exception as e:
            print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            print(f"ERROR: Could not write to CSV file: {e}")
            print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            flash('An error occurred while saving your data. Please contact support.', 'error')
            return redirect(url_for('questionnaire'))

    return render_template('questionnaire.html', questions_data=questions_data, options_data=options_data)

@app.route('/booking', methods=['GET', 'POST'])
# ... (booking route is unchanged)
def booking():
    if 'username' not in session: return redirect(url_for('login'))
    if request.method == 'POST':
        flash(f'Appointment booked!', 'success')
        return redirect(url_for('booking'))
    return render_template('booking.html', username=session['username'], timeslots=AVAILABLE_SLOTS)


@app.route('/logout')
# ... (logout route is unchanged)
def logout():
    session.pop('username', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('landing_page'))

COUNSELORS = {
    'dr.reid': 'psychology101',
    'ms.garcia': 'wellnesspass'
}

# Dummy list of appointments booked by students.
APPOINTMENTS = [
    {'student_name': 'Alex Johnson', 'date': '2025-09-18', 'time': '10:00 AM', 'notes': 'Anxiety over exams.'},
    {'student_name': 'Brenda Smith', 'date': '2025-09-18', 'time': '11:30 AM', 'notes': 'Career path discussion.'},
    {'student_name': 'Charles Davis', 'date': '2025-09-19', 'time': '02:00 PM', 'notes': 'Follow-up session.'},
    {'student_name': 'Diana Miller', 'date': '2025-09-20', 'time': '09:00 AM', 'notes': 'Initial consultation.'},
]

# --- ROUTES ---

# @app.route('/')
# def home():
#     """Redirects the home URL to the login page."""
#     return redirect(url_for('login'))

@app.route('/clogin', methods=['GET', 'POST'])
def clogin():
    """Handles the login process."""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if username exists and if the password matches
        if username in COUNSELORS and COUNSELORS[username] == password:
            session['username'] = username
            return redirect(url_for('view_appointments'))
        else:
            flash('Invalid username or password.', 'danger')
            # return redirect(url_for('clogin'))
            
    return render_template('clogin.html')

@app.route('/appointments')
def view_appointments():
    """Displays the list of appointments. Requires user to be logged in."""
    if 'username' in session:
        counselor_name = session['username']
        return render_template('appointments.html', appointments=APPOINTMENTS, counselor=counselor_name)
    else:
        # If not logged in, redirect them to the login page
        flash('You must be logged in to view that page.', 'danger')
        return redirect(url_for('login'))

@app.route('/clogout')
def clogout():
    """Logs the user out by clearing the session."""
    session.pop('username', None)
    flash('You have been successfully logged out.', 'success')
    return redirect(url_for('clogin'))

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    
    app.run(debug=True, host='0.0.0.0', port=5000)

