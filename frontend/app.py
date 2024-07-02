# app.py (Flask)

from flask import Flask, render_template, request, redirect, url_for, flash, session
import requests
import json

app = Flask(__name__)
app.secret_key = 'your_secret_key'

API_BASE_URL = 'http://localhost:7777'  # FastAPI backend URL

@app.route('/')
def index():
    if 'token' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('list_sets'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        response = requests.post(f"{API_BASE_URL}/token", data={'username': email, 'password': password})
        if response.status_code == 200:
            token_data = response.json()
            session['token'] = token_data['access_token']
            flash('Logged in successfully', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password', 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        nickname = request.form['nickname']
        password = request.form['password']
        response = requests.post(f"{API_BASE_URL}/register", json={'email': email, 'nickname': nickname, 'password': password})
        if response.status_code == 200:
            token_data = response.json()
            session['token'] = token_data['access_token']
            flash('Registered successfully', 'success')
            return redirect(url_for('index'))
        else:
            flash('Registration failed', 'error')
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('token', None)
    flash('Logged out successfully', 'success')
    return redirect(url_for('login'))

@app.route('/add_set', methods=['GET', 'POST'])
def add_set():
    if 'token' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        set_data = {
            'workout_id': int(request.form['workout_id']),
            'exercise_id': int(request.form['exercise_id']),
            'date': request.form['date'],
            'weight': float(request.form['weight']),
            'repetitions': int(request.form['repetitions'])
        }
        if request.form.get('rpe') and request.form['rpe'].strip():
            set_data['rpe'] = float(request.form['rpe'])
        if request.form.get('rir') and request.form['rir'].strip():
            set_data['rir'] = float(request.form['rir'])
        
        headers = {'Authorization': f"Bearer {session['token']}"}
        response = requests.post(f"{API_BASE_URL}/add_set_performed", json=set_data, headers=headers)
        if response.status_code == 200:
            flash('Set added successfully', 'success')
            return redirect(url_for('list_sets'))
        else:
            error_detail = response.json().get('detail', 'Unknown error')
            flash(f'Failed to add set: {error_detail}', 'error')
    
    # Fetch exercises and workouts for the form
    headers = {'Authorization': f"Bearer {session['token']}"}
    exercises = requests.get(f"{API_BASE_URL}/exercises", headers=headers).json()
    workouts = requests.get(f"{API_BASE_URL}/workouts", headers=headers).json()
    
    return render_template('add_set.html', exercises=exercises, workouts=workouts)

@app.route('/add_exercise', methods=['GET', 'POST'])
def add_exercise():
    if 'token' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        exercise_data = {
            'exercise_type': request.form['exercise_type'],
            'exercise_name': request.form['exercise_name']
        }
        headers = {'Authorization': f"Bearer {session['token']}"}
        response = requests.post(f"{API_BASE_URL}/add_exercise", json=exercise_data, headers=headers)
        if response.status_code == 200:
            flash('Exercise added successfully', 'success')
            return redirect(url_for('list_exercises'))
        else:
            flash('Failed to add exercise', 'error')
    
    return render_template('add_exercise.html')

@app.route('/create_block', methods=['GET', 'POST'])
def create_block():
    if 'token' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        block_data = {}
        if request.form['block_id']:
            block_data['id'] = int(request.form['block_id'])
        
        headers = {'Authorization': f"Bearer {session['token']}"}
        response = requests.post(f"{API_BASE_URL}/create_block", json=block_data, headers=headers)
        if response.status_code == 200:
            flash('Block created successfully', 'success')
            return redirect(url_for('list_workouts'))
        else:
            flash('Failed to create block', 'error')
    
    return render_template('create_block.html')

@app.route('/create_workout', methods=['GET', 'POST'])
def create_workout():
    if 'token' not in session:
        return redirect(url_for('login'))
    
    headers = {'Authorization': f"Bearer {session['token']}"}

    if request.method == 'POST':
        workout_data = {
            'block_id': int(request.form['block_id'])
        }
        if request.form['workout_id']:
            workout_data['id'] = int(request.form['workout_id'])
        
        headers = {'Authorization': f"Bearer {session['token']}"}
        response = requests.post(f"{API_BASE_URL}/create_workout", json=workout_data, headers=headers)
        if response.status_code == 200:
            flash('Workout created successfully', 'success')
            return redirect(url_for('list_workouts'))
        else:
            flash('Failed to create workout', 'error')
    
    # Fetch blocks for the form
    response = requests.get(f"{API_BASE_URL}/blocks", headers=headers)
    if response.status_code == 200:
        blocks = response.json()
    else:
        blocks = []
        flash('Failed to fetch blocks', 'error')
    
    return render_template('create_workout.html', blocks=blocks)

@app.route('/list_sets')
def list_sets():
    if 'token' not in session:
        return redirect(url_for('login'))
    
    headers = {'Authorization': f"Bearer {session['token']}"}
    response = requests.get(f"{API_BASE_URL}/sets", headers=headers)
    if response.status_code == 200:
        sets = response.json()
        # Fetch exercise names
        exercise_response = requests.get(f"{API_BASE_URL}/exercises", headers=headers)
        if exercise_response.status_code == 200:
            exercises = {ex['id']: ex['exercise_name'] for ex in exercise_response.json()}
            for set in sets:
                set['exercise_name'] = exercises.get(set['exercise_id'], 'Unknown')
        else:
            flash('Failed to fetch exercise names', 'error')
    else:
        sets = []
        flash('Failed to fetch sets', 'error')
    return render_template('list_sets.html', sets=sets)

@app.route('/list_workouts')
def list_workouts():
    if 'token' not in session:
        return redirect(url_for('login'))
    
    headers = {'Authorization': f"Bearer {session['token']}"}
    response = requests.get(f"{API_BASE_URL}/workouts", headers=headers)
    if response.status_code == 200:
        workouts = response.json()
        return render_template('list_workouts.html', workouts=workouts)
    else:
        flash('Failed to fetch workouts', 'error')
        return redirect(url_for('index'))

@app.route('/list_exercises')
def list_exercises():
    if 'token' not in session:
        return redirect(url_for('login'))
    
    headers = {'Authorization': f"Bearer {session['token']}"}
    response = requests.get(f"{API_BASE_URL}/exercises", headers=headers)
    if response.status_code == 200:
        exercises = response.json()
        return render_template('list_exercises.html', exercises=exercises)
    else:
        flash('Failed to fetch exercises', 'error')
        return redirect(url_for('index'))

@app.route('/list_blocks')
def list_blocks():
    if 'token' not in session:
        return redirect(url_for('login'))
    
    headers = {'Authorization': f"Bearer {session['token']}"}
    response = requests.get(f"{API_BASE_URL}/blocks", headers=headers)
    if response.status_code == 200:
        blocks = response.json()
    else:
        blocks = []
        flash('Failed to fetch blocks', 'error')
    return render_template('list_blocks.html', blocks=blocks)

if __name__ == '__main__':
    app.run(debug=True)