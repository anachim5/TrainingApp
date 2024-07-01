from flask import Flask, render_template, request, redirect, url_for, flash
import requests
import json
from datetime import date

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a real secret key

API_BASE_URL = 'http://localhost:7777'  # Replace with your FastAPI base URL

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/create_user', methods=['GET', 'POST'])
def create_user():
    if request.method == 'POST':
        data = {
            'nickname': request.form['nickname'],
            'email': request.form['email']
        }
        response = requests.post(f'{API_BASE_URL}/users', json=data)
        if response.status_code == 200:
            flash('User created successfully!', 'success')
        else:
            flash('Error creating user.', 'error')
        return redirect(url_for('create_user'))
    return render_template('create_user.html')


@app.route('/add_exercise', methods=['GET', 'POST'])
def add_exercise():
    if request.method == 'POST':
        data = {
            'exercise_type': request.form['exercise_type'],
            'exercise_name': request.form['exercise_name'],
            'user_id': int(request.form['user_id'])
        }
        response = requests.post(f'{API_BASE_URL}/add_exercise', json=data)
        if response.status_code == 200:
            flash('Exercise added successfully!', 'success')
        else:
            flash('Error adding exercise.', 'error')
        return redirect(url_for('add_exercise'))
    return render_template('add_exercise.html')

@app.route('/create_block', methods=['GET', 'POST'])
def create_block():
    if request.method == 'POST':
        data = {
            'user_id': int(request.form['user_id'])
        }
        response = requests.post(f'{API_BASE_URL}/create_block', json=data)
        if response.status_code == 200:
            flash('Block created successfully!', 'success')
        else:
            flash('Error creating block.', 'error')
        return redirect(url_for('create_block'))
    return render_template('create_block.html')

@app.route('/create_workout', methods=['GET', 'POST'])
def create_workout():
    if request.method == 'POST':
        data = {
            'user_id': int(request.form['user_id']),
            'block_id': int(request.form['block_id'])
        }
        response = requests.post(f'{API_BASE_URL}/create_workout', json=data)
        if response.status_code == 200:
            flash('Workout created successfully!', 'success')
        else:
            flash('Error creating workout.', 'error')
        return redirect(url_for('create_workout'))
    return render_template('create_workout.html')

@app.route('/list_sets')
def list_sets():
    response = requests.get(f'{API_BASE_URL}/sets')
    if response.status_code == 200:
        sets = response.json()
        return render_template('list_sets.html', sets=sets)
    flash('Error fetching sets.', 'error')
    return render_template('list_sets.html', sets=[])

@app.route('/list_workouts')
def list_workouts():
    response = requests.get(f'{API_BASE_URL}/workouts')
    if response.status_code == 200:
        workouts = response.json()
        return render_template('list_workouts.html', workouts=workouts)
    flash('Error fetching workouts.', 'error')
    return render_template('list_workouts.html', workouts=[])

@app.route('/list_exercises')
def list_exercises():
    response = requests.get(f'{API_BASE_URL}/exercises')
    if response.status_code == 200:
        exercises = response.json()
        return render_template('list_exercises.html', exercises=exercises)
    flash('Error fetching exercises.', 'error')
    return render_template('list_exercises.html', exercises=[])

@app.route('/add_set_performed', methods=['GET', 'POST'])
def add_set_performed():
    if request.method == 'POST':
        try:
            user_id = request.form.get('user_id')
            workout_id = request.form.get('workout_id')
            exercise_id = request.form.get('exercise_id')
            
            if not user_id or not workout_id or not exercise_id:
                raise ValueError("User, Workout, and Exercise must be selected")
            
            data = {
                'user_id': int(user_id),
                'workout_id': int(workout_id),
                'date': request.form['date'],
                'exercise_id': int(exercise_id),
                'weight': float(request.form['weight']),
                'repetitions': int(request.form['repetitions']),
                'RPE': float(request.form['RPE']) if request.form['RPE'] else None,
                'RIR': float(request.form['RIR']) if request.form['RIR'] else None
            }
            response = requests.post(f'{API_BASE_URL}/add_set_performed', json=data)
            if response.status_code == 200:
                flash('Set performed added successfully!', 'success')
            else:
                flash(f'Error adding set performed: {response.text}', 'error')
        except ValueError as e:
            flash(f'Invalid input: {str(e)}', 'error')
        except requests.RequestException as e:
            flash(f'Error communicating with the server: {str(e)}', 'error')
        return redirect(url_for('add_set_performed'))

    users = requests.get(f'{API_BASE_URL}/users').json()
    exercises = requests.get(f'{API_BASE_URL}/exercises').json()

    # Set the first user as default if no user is selected
    selected_user_id = request.args.get('user_id') or (users[0]['user_id'] if users else None)
    
    workouts = []
    if selected_user_id:
        workouts = requests.get(f'{API_BASE_URL}/user/{selected_user_id}/workouts').json()

    exercise_id = request.args.get('exercise_id')
    exercise_type = request.args.get('exercise_type')
    exercise_name = request.args.get('exercise_name')

    if exercise_id or exercise_type or exercise_name:
        params = {}
        if exercise_id:
            params['exercise_id'] = exercise_id
        if exercise_type:
            params['exercise_type'] = exercise_type
        if exercise_name:
            params['exercise_name'] = exercise_name
        exercises = requests.get(f'{API_BASE_URL}/exercises', params=params).json()

    # Define the available exercise types
    exercise_types = ["COMP", "VARIATION", "ACCESSORY"]

    return render_template('add_set_performed.html', 
                           users=users, 
                           workouts=workouts, 
                           exercises=exercises, 
                           today=date.today(),
                           selected_user_id=selected_user_id,
                           exercise_types=exercise_types)

if __name__ == '__main__':
    app.run(debug=True)