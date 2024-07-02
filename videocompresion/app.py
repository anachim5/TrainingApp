from flask import Flask, render_template, request, redirect
import requests

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        workout_id = request.form['workout_id']
        set_id = request.form['set_id']
        file = request.files['file']

        # Send file to FastAPI backend
        files = {'file': (file.filename, file.stream, file.mimetype)}
        data = {'workout_id': workout_id, 'set_id': set_id}
        response = requests.post("http://127.0.0.1:7520/upload/", files=files, data=data)

        if response.status_code == 200:
            return redirect('/')
    return render_template('upload.html')

@app.route('/videos')
def list_videos():
    response = requests.get("http://127.0.0.1:7520/videos/")
    if response.status_code == 200:
        videos = response.json()
        return render_template('videos.html', videos=videos)
    return "Failed to fetch videos"

if __name__ == '__main__':
    app.run(debug=True)
