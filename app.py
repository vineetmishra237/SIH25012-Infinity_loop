import os
import cv2
import insightface
import numpy as np
from flask import Flask, request, jsonify, send_from_directory, Response
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import json
from datetime import datetime, timezone 
import queue

app = Flask(__name__)
CORS(app)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'attendance.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- InsightFace Model Initialization ---
# This section loads the pre-trained model for face analysis.
print("Loading InsightFace model... This may take a moment.")
try:
    # We specify 'CPUExecutionProvider' to ensure it runs on standard hardware without a dedicated GPU.
    face_analysis_app = insightface.app.FaceAnalysis(providers=['CPUExecutionProvider'])
    face_analysis_app.prepare(ctx_id=0, det_size=(640, 640))
    print("✅ InsightFace model loaded successfully.")
except Exception as e:
    print(f"❌ Critical Error: Could not load InsightFace model. Error: {e}")
    print("Please ensure you have run 'pip install -r requirements.txt' and that onnxruntime is installed correctly.")
    exit()

# --- Real-time Event Streaming Queue ---
# This queue holds RFID scan events to be pushed to the web client.
sse_queue = queue.Queue()

# --- Database Models ---
# Defines the structure of the tables in our database.

class Student(db.Model):
    """Represents an enrolled student."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    roll_number = db.Column(db.String(50), unique=True, nullable=False)
    rfid_uid = db.Column(db.String(50), unique=True, nullable=False)
    # Establishes a relationship to the face encoding table.
    face_encoding = db.relationship('FaceEncoding', backref='student', uselist=False, cascade="all, delete-orphan")

    def to_dict(self):
        """Converts the Student object to a dictionary for API responses."""
        return {'id': self.id, 'name': self.name, 'roll_number': self.roll_number, 'rfid_uid': self.rfid_uid}

class FaceEncoding(db.Model):
    """Stores the mathematical representation (embedding) of a student's face."""
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False, unique=True)
    # The face embedding is stored as a JSON string.
    encoding_json = db.Column(db.Text, nullable=False)

class AttendanceLog(db.Model):
    """Records each successful attendance event."""
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    # Links back to the Student model to easily retrieve student info.
    student_rel = db.relationship('Student', backref=db.backref('logs', lazy=True))

    def to_dict(self):
        """Converts the log object to a dictionary."""
        # ✅ FIXED: Make the timestamp timezone-aware (UTC) before sending to the frontend.
        # This allows JavaScript to easily convert it to the user's local time.
        utc_timestamp = self.timestamp.replace(tzinfo=timezone.utc)
        return {
            'id': self.id, 
            'student_name': self.student_rel.name, 
            'student_roll_number': self.student_rel.roll_number, 
            'timestamp': utc_timestamp.isoformat() # Now sends a standard format like '...Z' or '...+00:00'
        }

# --- Helper Function ---
def calculate_similarity(embedding1, embedding2):
    """Calculates cosine similarity between two face embeddings."""
    # Cosine similarity is a measure of similarity between two non-zero vectors.
    return np.dot(embedding1, embedding2) / (np.linalg.norm(embedding1) * np.linalg.norm(embedding2))

# --- API Endpoints ---

@app.route('/')
def index():
    """Serves the main index.html file."""
    return send_from_directory('.', 'index.html')

@app.route('/api/enroll', methods=['POST'])
def enroll_student():
    """Handles new student enrollment."""
    # Check if all required form fields are present.
    if 'name' not in request.form or 'roll_number' not in request.form or 'rfid_uid' not in request.form or 'face_image' not in request.files:
        return jsonify({'error': 'Missing form data or face image'}), 400

    rfid_uid = request.form['rfid_uid'].lower()
    # Prevent duplicates by checking for existing roll number or RFID UID.
    if Student.query.filter((Student.roll_number == request.form['roll_number']) | (Student.rfid_uid == rfid_uid)).first():
        return jsonify({'error': 'Student with this Roll Number or RFID UID already exists'}), 409

    file = request.files['face_image']
    try:
        # Convert the uploaded image file into a format OpenCV can read.
        npimg = np.frombuffer(file.read(), np.uint8)
        img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
        
        # Use InsightFace to detect and analyze faces in the image.
        faces = face_analysis_app.get(img)

        if not faces: return jsonify({'error': 'No face found in the image.'}), 400
        if len(faces) > 1: return jsonify({'error': 'More than one face found. Please capture a clear photo of one person.'}), 400
        
        # Extract the face embedding (the mathematical vector).
        student_embedding = faces[0].embedding
    except Exception as e:
        return jsonify({'error': f'Could not process image: {str(e)}'}), 500

    # Create and save the new student and their face encoding to the database.
    new_student = Student(name=request.form['name'], roll_number=request.form['roll_number'], rfid_uid=rfid_uid)
    db.session.add(new_student)
    db.session.commit() # Commit to get the new_student.id

    new_encoding = FaceEncoding(student_id=new_student.id, encoding_json=json.dumps(student_embedding.tolist()))
    db.session.add(new_encoding)
    db.session.commit()

    return jsonify({'message': f"Student '{new_student.name}' enrolled successfully!", 'student': new_student.to_dict()}), 201

@app.route('/api/rfid_scan', methods=['POST'])
def rfid_scan():
    """Receives UID from the ESP8266 and triggers a real-time event."""
    data = request.get_json()
    if not data or 'uid' not in data:
        return jsonify({'error': 'Invalid request. UID is required.'}), 400
    
    uid = data['uid'].lower()
    student = Student.query.filter_by(rfid_uid=uid).first()
    
    # Prepare the event data to be sent to the frontend.
    event_data = {'uid': uid}
    if student:
        event_data.update({'name': student.name, 'status': 'registered'})
    else:
        event_data.update({'name': 'Unknown', 'status': 'unregistered'})

    # Put the event data into the queue for the streamer to pick up.
    sse_queue.put(json.dumps(event_data))
    return jsonify({'status': 'UID received and event queued'}), 200

@app.route('/api/stream')
def stream():
    """Endpoint for Server-Sent Events (SSE) to push live updates."""
    def event_stream():
        while True:
            # Wait for a message in the queue and send it to the client.
            message = sse_queue.get()
            yield f"data: {message}\n\n"
    return Response(event_stream(), mimetype='text/event-stream')

@app.route('/api/verify_attendance', methods=['POST'])
def verify_attendance():
    """Verifies the live face against the stored face for the given RFID."""
    if 'rfid_uid' not in request.form or 'live_image' not in request.files:
        return jsonify({'error': 'Missing RFID UID or live image'}), 400

    rfid_uid = request.form['rfid_uid'].lower()
    student = Student.query.filter_by(rfid_uid=rfid_uid).first()
    if not student:
        return jsonify({'match': False, 'reason': 'RFID card not registered.'}), 404

    # Load the stored face embedding from the database.
    stored_encoding = np.array(json.loads(student.face_encoding.encoding_json))
    
    try:
        # Process the live image from the webcam feed.
        npimg = np.frombuffer(request.files['live_image'].read(), np.uint8)
        live_image = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
        live_faces = face_analysis_app.get(live_image)

        if not live_faces:
            return jsonify({'match': False, 'reason': 'No face detected in camera feed.'}), 400

        # Calculate similarity between the stored face and the live face.
        similarity = calculate_similarity(stored_encoding, live_faces[0].embedding)
        VERIFICATION_THRESHOLD = 0.4 # This threshold can be tuned. Higher means stricter matching.

        if similarity > VERIFICATION_THRESHOLD:
            # ✅ FIXED: Use UTC to define "today" for consistent logic.
            today_start = datetime.combine(datetime.utcnow().date(), datetime.min.time())
            if AttendanceLog.query.filter(AttendanceLog.student_id == student.id, AttendanceLog.timestamp >= today_start).first():
                return jsonify({'match': True, 'reason': 'Attendance already marked for today.', 'student_name': student.name}), 208 # 208 = Already Reported
            
            # Log the new attendance record.
            new_log = AttendanceLog(student_id=student.id)
            db.session.add(new_log)
            db.session.commit()
            return jsonify({'match': True, 'reason': f'Welcome, {student.name}!', 'student_name': student.name}), 200
        else:
            return jsonify({'match': False, 'reason': 'Face does not match profile.', 'student_name': student.name}), 401 # 401 = Unauthorized
            
    except Exception as e:
        return jsonify({'error': f'Verification process failed: {str(e)}'}), 500

@app.route('/api/attendance/summary', methods=['GET'])
def get_attendance_summary():
    """Provides statistics for the dashboard."""
    total_students = Student.query.count()
    # ✅ FIXED: Use UTC to define "today" for consistent logic.
    today_start = datetime.combine(datetime.utcnow().date(), datetime.min.time())
    
    # Find all unique students who have a log entry today.
    present_student_ids = {log.student_id for log in AttendanceLog.query.filter(AttendanceLog.timestamp >= today_start).all()}
    present_today_count = len(present_student_ids)

    return jsonify({
        'total_students': total_students,
        'present_today': present_today_count,
        'absent_today': total_students - present_today_count
    })

@app.route('/api/students', methods=['GET'])
def get_students():
    """Returns a list of all enrolled students."""
    students = Student.query.order_by(Student.name).all()
    return jsonify([s.to_dict() for s in students])

@app.route('/api/attendance', methods=['GET'])
def get_attendance_logs():
    """Returns all attendance logs, newest first."""
    logs = AttendanceLog.query.order_by(AttendanceLog.timestamp.desc()).all()
    return jsonify([log.to_dict() for log in logs])

# --- Main Execution Block ---
if __name__ == '__main__':
    with app.app_context():
        # This creates the database and tables if they don't exist.
        db.create_all()
    # Running with debug=True provides helpful error messages during development.
    # host='0.0.0.0' makes the server accessible from other devices on the network.
    app.run(host='0.0.0.0', port=5000, debug=True)