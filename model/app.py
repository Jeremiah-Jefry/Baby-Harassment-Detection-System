from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import os
import json
from datetime import datetime
from threading import Thread
import time
import random
import torch
from model_3dcnn import Simple3DCNN   # your 3D CNN class

ckpt_path = "checkpoints/best_model.pt"   # or final_model.pt
ckpt = torch.load(ckpt_path, map_location="cpu")

label2idx = ckpt["label2idx"]
idx2label = ckpt["idx2label"]
num_classes = len(label2idx)

model = Simple3DCNN(num_classes)
model.load_state_dict(ckpt["model_state_dict"])
model.eval()


app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-in-production'

# Upload configuration
app.config['UPLOAD_FOLDER'] = 'uploads/videos'
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv'}

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ── Persistent user storage ──
USERS_FILE = 'users.json'

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_users(data):
    with open(USERS_FILE, 'w') as f:
        json.dump(data, f, indent=2)

users_data = load_users()

# ── Camera & alert data ──
cameras_data = {
    'CAM001': {'name': 'Baby Room - Main',  'status': 'active',   'recording': True,  'location': 'Baby Room', 'ip_address': '192.168.1.101'},
    'CAM002': {'name': 'Nursery Corner',    'status': 'active',   'recording': True,  'location': 'Nursery',   'ip_address': '192.168.1.102'},
    'CAM003': {'name': 'Kitchen View',      'status': 'inactive', 'recording': False, 'location': 'Kitchen',   'ip_address': '192.168.1.103'},
    'CAM004': {'name': 'Living Hall',       'status': 'active',   'recording': False, 'location': 'Hall',      'ip_address': '192.168.1.104'},
    'CAM005': {'name': 'Play Area',         'status': 'active',   'recording': True,  'location': 'Play Room', 'ip_address': '192.168.1.105'},
    'CAM006': {'name': 'Feeding Zone',      'status': 'inactive', 'recording': False, 'location': 'Dining',    'ip_address': '192.168.1.106'},
}

alerts_data = [
    {'id': 1, 'message': 'Motion detected in Baby Room',  'time': '10:30 AM', 'type': 'warning'},
    {'id': 2, 'message': 'Camera CAM003 went offline',    'time': '09:15 AM', 'type': 'critical'},
    {'id': 3, 'message': 'Recording started in Nursery',  'time': '08:00 AM', 'type': 'info'},
]

video_analysis_results = {}

APP_PASSWORD = "PyVision"

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ==================== MOCK VIDEO ANALYSIS ====================

def mock_analyze_video(video_path, video_id):
    try:
        print(f"[MockAnalysis] Starting for: {video_path}")

        simulated_duration = round(random.uniform(30, 180), 2)
        simulated_fps      = random.choice([24, 25, 30])
        simulated_frames   = int(simulated_duration * simulated_fps)

        for progress in range(0, 101, 10):
            time.sleep(0.6)
            video_analysis_results[video_id] = {
                'status':   'processing',
                'progress': progress,
                'message':  f'Analysing video… {progress}% complete'
            }

        alerts = []

        num_motion = random.randint(0, 6)
        for i in range(num_motion):
            ts = round(random.uniform(1, simulated_duration), 2)
            alerts.append({
                'type':      'motion',
                'severity':  'warning',
                'message':   f'High motion detected at {ts}s',
                'timestamp': ts,
                'frame':     int(ts * simulated_fps)
            })

        if random.random() < 0.3:
            ts = round(random.uniform(1, simulated_duration), 2)
            alerts.append({
                'type':      'crying',
                'severity':  'critical',
                'message':   f'Potential baby distress detected at {ts}s',
                'timestamp': ts,
                'frame':     int(ts * simulated_fps)
            })

        alerts.sort(key=lambda a: a['timestamp'])

        critical_alerts = [a for a in alerts if a['severity'] == 'critical']
        warning_alerts  = [a for a in alerts if a['severity'] == 'warning']

        if critical_alerts:
            status  = 'critical'
            message = f'⚠️ CRITICAL: {len(critical_alerts)} critical alert(s) detected! Baby may need immediate attention.'
        elif len(warning_alerts) > 3:
            status  = 'warning'
            message = f'⚠️ WARNING: {len(warning_alerts)} motion alert(s) detected. Please review the footage.'
        else:
            status  = 'safe'
            message = '✅ Video analysis complete. No critical issues detected.'

        summary = {
            'total_frames':         simulated_frames,
            'duration':             simulated_duration,
            'motion_detected':      num_motion > 0,
            'high_motion_frames':   num_motion * random.randint(3, 8),
            'face_detected_frames': random.randint(0, simulated_frames // 10),
            'alerts':               alerts
        }

        video_analysis_results[video_id] = {
            'status':     status,
            'message':    message,
            'summary':    summary,
            'alerts':     alerts,
            'timestamp':  datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'video_path': video_path,
            'note':       'Analysis performed using mock engine (OpenCV not installed).'
        }

        if status == 'critical':
            alerts_data.insert(0, {
                'id':      len(alerts_data) + 1,
                'message': 'Critical: Baby distress detected in uploaded video',
                'time':    datetime.now().strftime('%I:%M %p'),
                'type':    'critical'
            })

        print(f"[MockAnalysis] Complete for {video_id}: {status}")

    except Exception as e:
        print(f"[MockAnalysis] Error: {e}")
        video_analysis_results[video_id] = {
            'status':    'error',
            'message':   f'Error during analysis: {str(e)}',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }


def process_video_async(video_path, video_id):
    thread = Thread(target=mock_analyze_video, args=(video_path, video_id))
    thread.daemon = True
    thread.start()


# ==================== ROUTES ====================

@app.route('/')
def index():
    return render_template('splash.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/submit_login', methods=['POST'])
def submit_login():
    email    = request.form.get('email', '').strip()
    password = request.form.get('password', '').strip()

    if not email:
        return render_template('login.html', error='Please enter your email.')

    if email not in users_data:
        return render_template('login.html', error='Not a registered mail ID. Please register first.')

    session['user'] = email
    return redirect(url_for('dashboard'))

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/submit_register', methods=['POST'])
def submit_register():
    global users_data
    data         = request.form
    email        = data.get('email', '').strip()
    app_password = data.get('app_password', '').strip()

    if not email:
        return render_template('register.html', error='Please enter your email.')

    if email in users_data:
        return render_template('register.html', error='This email is already registered. Please sign in.')

    if app_password != APP_PASSWORD:
        return render_template('register.html', error='Incorrect App Password. Please try again.')

    users_data[email] = {
        'parent_name':    data.get('parent_name'),
        'mobile':         data.get('mobile'),
        'email':          email,
        'mail_password':  data.get('mail_password'),
        'address':        data.get('address'),
        'camera_ip':      data.get('camera_ip'),
        'registered_at':  datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'backup_contacts': [],
        'alert_numbers':   [],
        'settings': {
            'alerts_enabled':    True,
            'sms_enabled':       True,
            'email_enabled':     False,
            'push_enabled':      False,
            'auto_record':       True,
            'continuous_record': False,
        }
    }

    save_users(users_data)

    session['user'] = email
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    user_data = users_data.get(session['user'], {})
    return render_template('dashboard.html', user=user_data)

@app.route('/camera-management')
def camera_management():
    if 'user' not in session:
        return redirect(url_for('login'))

    total_cameras     = len(cameras_data)
    online_cameras    = sum(1 for c in cameras_data.values() if c['status'] == 'active')
    offline_cameras   = total_cameras - online_cameras
    recording_cameras = sum(1 for c in cameras_data.values() if c['recording'])

    stats = {
        'total':     total_cameras,
        'online':    online_cameras,
        'offline':   offline_cameras,
        'recording': recording_cameras
    }

    user_data = users_data.get(session['user'], {})
    return render_template('camera_management.html',
                           user=user_data,
                           cameras=cameras_data,
                           stats=stats,
                           alerts=alerts_data)

@app.route('/add-camera')
def add_camera():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('add_camera.html')

@app.route('/submit-camera', methods=['POST'])
def submit_camera():
    if 'user' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401

    try:
        data = request.get_json()

        camera_id   = data.get('camera_id',   '').strip().upper()
        camera_name = data.get('camera_name', '').strip()
        location    = data.get('location',    '').strip()
        ip_address  = data.get('ip_address',  '').strip()

        if not all([camera_id, camera_name, location, ip_address]):
            return jsonify({'success': False, 'message': 'All fields are required'}), 400

        if camera_id in cameras_data:
            return jsonify({'success': False, 'message': 'Camera ID already exists'}), 400

        cameras_data[camera_id] = {
            'name':       camera_name,
            'location':   location,
            'ip_address': ip_address,
            'status':     'active',
            'recording':  False
        }

        alerts_data.insert(0, {
            'id':      len(alerts_data) + 1,
            'message': f'New camera {camera_id} added to {location}',
            'time':    datetime.now().strftime('%I:%M %p'),
            'type':    'info'
        })

        return jsonify({'success': True, 'message': 'Camera added successfully!', 'camera_id': camera_id})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/delete-camera/<camera_id>', methods=['DELETE'])
def delete_camera(camera_id):
    if 'user' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401

    if camera_id not in cameras_data:
        return jsonify({'success': False, 'message': 'Camera not found'}), 404

    camera_name = cameras_data[camera_id]['name']
    del cameras_data[camera_id]

    alerts_data.insert(0, {
        'id':      len(alerts_data) + 1,
        'message': f'Camera {camera_id} ({camera_name}) was removed',
        'time':    datetime.now().strftime('%I:%M %p'),
        'type':    'warning'
    })

    return jsonify({'success': True, 'message': f'Camera {camera_id} deleted successfully'})

@app.route('/video-input')
def video_input():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('video_input.html')

@app.route('/upload-video', methods=['POST'])
def upload_video():
    if 'user' not in session:
        return redirect(url_for('login'))

    if 'video' not in request.files:
        flash('No video file selected', 'error')
        return redirect(url_for('video_input'))

    file = request.files['video']

    if file.filename == '':
        flash('No video file selected', 'error')
        return redirect(url_for('video_input'))

    if file and allowed_file(file.filename):
        filename        = secure_filename(file.filename)
        timestamp       = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{timestamp}_{filename}"
        filepath        = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)

        try:
            file.save(filepath)

            video_id = f"video_{timestamp}"

            video_analysis_results[video_id] = {
                'status':    'queued',
                'message':   'Video uploaded successfully. Analysis starting…',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

            process_video_async(filepath, video_id)
            session['last_video_id'] = video_id

            flash('Video uploaded successfully! Analysis in progress…', 'success')
            return redirect(url_for('video_results', video_id=video_id))

        except Exception as e:
            flash(f'Error uploading video: {str(e)}', 'error')
            return redirect(url_for('video_input'))
    else:
        flash('Invalid file format. Please upload MP4, AVI, MOV, or MKV files.', 'error')
        return redirect(url_for('video_input'))

@app.route('/upload-video-url', methods=['POST'])
def upload_video_url():
    if 'user' not in session:
        return redirect(url_for('login'))

    video_url  = request.form.get('video_url')
    video_name = request.form.get('video_name', 'Unnamed Video')

    if not video_url:
        flash('Please provide a video URL', 'error')
        return redirect(url_for('video_input'))

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    video_id  = f"video_url_{timestamp}"

    video_analysis_results[video_id] = {
        'status':    'processing',
        'message':   'Processing video from URL…',
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    flash('Video URL submitted. Note: URL processing requires additional setup.', 'info')
    return redirect(url_for('video_results', video_id=video_id))

@app.route('/video-results/<video_id>')
def video_results(video_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    user_data = users_data.get(session['user'], {})
    return render_template('video_results.html', video_id=video_id, user=user_data)

@app.route('/api/video-status/<video_id>')
def video_status(video_id):
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401

    if video_id not in video_analysis_results:
        return jsonify({'status': 'not_found', 'message': 'Video analysis not found'}), 404

    return jsonify(video_analysis_results[video_id])

@app.route('/alerts')
def alerts():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('alerts.html', alerts=alerts_data)

@app.route('/settings')
def settings():
    if 'user' not in session:
        return redirect(url_for('login'))
    user_data = users_data.get(session['user'], {})
    return render_template('settings.html', user=user_data)


# ==================== UPDATE SETTINGS ====================

@app.route('/update-settings', methods=['POST'])
def update_settings():
    if 'user' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401

    data         = request.get_json()
    setting_type = data.get('type')
    user_email   = session['user']

    # Make sure this user exists
    if user_email not in users_data:
        return jsonify({'success': False, 'message': 'User not found'}), 404

    user = users_data[user_email]

    # Ensure nested keys exist for old accounts
    if 'settings' not in user:
        user['settings'] = {
            'alerts_enabled':    True,
            'sms_enabled':       True,
            'email_enabled':     False,
            'push_enabled':      False,
            'auto_record':       True,
            'continuous_record': False,
        }
    if 'backup_contacts' not in user:
        user['backup_contacts'] = []
    if 'alert_numbers' not in user:
        user['alert_numbers'] = []

    # ── Toggle (alert preferences & recording) ──
    if setting_type == 'toggle':
        key   = data.get('key')
        value = data.get('value')
        allowed_keys = {
            'alerts_enabled', 'sms_enabled', 'email_enabled',
            'push_enabled', 'auto_record', 'continuous_record'
        }
        if key not in allowed_keys:
            return jsonify({'success': False, 'message': 'Invalid setting key'}), 400
        user['settings'][key] = value
        save_users(users_data)
        return jsonify({'success': True, 'message': 'Setting updated'})

    # ── Username ──
    if setting_type == 'username':
        new_username = data.get('username', '').strip()
        if not new_username:
            return jsonify({'success': False, 'message': 'Username cannot be empty'})
        if len(new_username) < 2:
            return jsonify({'success': False, 'message': 'Username must be at least 2 characters'})
        user['parent_name'] = new_username
        save_users(users_data)
        return jsonify({
            'success':   True,
            'message':   'Username updated successfully',
            'new_value': new_username
        })

    # ── Password ──
    if setting_type == 'password':
        current_pw = data.get('current_password', '').strip()
        new_pw     = data.get('new_password', '').strip()

        if not current_pw or not new_pw:
            return jsonify({'success': False, 'message': 'Both fields are required'})

        if len(new_pw) < 6:
            return jsonify({'success': False, 'message': 'New password must be at least 6 characters'})

        # If password is stored as a hash, use check_password_hash
        stored_pw = user.get('mail_password', '')
        if stored_pw and stored_pw != current_pw:
            return jsonify({'success': False, 'message': 'Current password is incorrect'})

        # Store new password (plain text matches your existing pattern)
        user['mail_password'] = new_pw
        save_users(users_data)
        return jsonify({'success': True, 'message': 'Password updated successfully'})

    # ── Email ──
    if setting_type == 'email':
        new_email = data.get('email', '').strip().lower()
        if not new_email or '@' not in new_email or '.' not in new_email:
            return jsonify({'success': False, 'message': 'Please enter a valid email address'})
        if new_email != user_email and new_email in users_data:
            return jsonify({'success': False, 'message': 'This email is already in use'})

        # Update the key in users_data dict if email changed
        if new_email != user_email:
            users_data[new_email] = users_data.pop(user_email)
            users_data[new_email]['email'] = new_email
            session['user'] = new_email
        else:
            user['email'] = new_email

        save_users(users_data)
        return jsonify({
            'success':   True,
            'message':   'Email updated successfully',
            'new_value': new_email
        })

    # ── Phone number ──
    if setting_type == 'phone':
        new_mobile = data.get('mobile', '').strip()
        if not new_mobile:
            return jsonify({'success': False, 'message': 'Phone number cannot be empty'})
        user['mobile'] = new_mobile
        save_users(users_data)
        return jsonify({
            'success':   True,
            'message':   'Phone number updated successfully',
            'new_value': new_mobile
        })

    # ── Parent phone ──
    if setting_type == 'parent_phone':
        phone = data.get('parent_phone', '').strip()
        if not phone:
            return jsonify({'success': False, 'message': 'Please enter a phone number'})
        user['parent_phone'] = phone
        # Also update mobile if not already set
        if not user.get('mobile'):
            user['mobile'] = phone
        save_users(users_data)
        return jsonify({
            'success':   True,
            'message':   'Parent phone number saved',
            'new_value': phone
        })

    # ── Backup contact ──
    if setting_type == 'backup_contact':
        contact_name  = data.get('contact_name', '').strip()
        contact_phone = data.get('contact_phone', '').strip()
        if not contact_name or not contact_phone:
            return jsonify({'success': False, 'message': 'Name and phone number are both required'})

        # Prevent duplicate phone numbers
        existing = [c['phone'] for c in user['backup_contacts']]
        if contact_phone in existing:
            return jsonify({'success': False, 'message': 'This number is already saved as a backup contact'})

        user['backup_contacts'].append({
            'name':       contact_name,
            'phone':      contact_phone,
            'added_at':   datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        save_users(users_data)
        return jsonify({
            'success':       True,
            'message':       f'{contact_name} added as backup contact',
            'contact_name':  contact_name,
            'contact_phone': contact_phone
        })

    # ── Multi alert numbers ──
    if setting_type == 'multi_alert':
        numbers_raw = data.get('numbers', '')
        number_list = [n.strip() for n in numbers_raw.split('\n') if n.strip()]
        if not number_list:
            return jsonify({'success': False, 'message': 'Please enter at least one phone number'})

        user['alert_numbers'] = number_list
        save_users(users_data)
        return jsonify({
            'success': True,
            'message': f'{len(number_list)} number(s) saved for alerts'
        })

    return jsonify({'success': False, 'message': 'Unknown setting type'}), 400


# ==================== RUN ====================

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)