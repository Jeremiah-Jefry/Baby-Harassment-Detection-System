import os

templates_dir = 'c:/Users/KiTE/Desktop/model/templates'
static_dir = 'c:/Users/KiTE/Desktop/model/static'

files_to_create = {
    # HTML Templates
    f'{templates_dir}/login.html': '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login - Guardian Eyes</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='login.css') }}">
</head>
<body>
    <div class="login-container">
        <div class="login-box">
            <h1>Welcome Back</h1>
            <p class="subtitle">Sign in to continue</p>
            <form action="/submit_login" method="POST">
                <div class="form-group">
                    <label for="email">Email</label>
                    <input type="email" id="email" name="email" required>
                </div>
                <div class="form-group">
                    <label for="password">Password</label>
                    <input type="password" id="password" name="password" required>
                </div>
                <button type="submit" class="btn-primary">Sign In</button>
            </form>
            <p class="register-link">Don't have an account? <a href="/register">Register</a></p>
        </div>
    </div>
</body>
</html>''',

    f'{templates_dir}/register.html': '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Register - Guardian Eyes</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='register.css') }}">
</head>
<body>
    <div class="register-container">
        <div class="register-box">
            <h1>Create Account</h1>
            <form action="/submit_register" method="POST">
                <div class="form-group">
                    <label for="parent_name">Parent Name</label>
                    <input type="text" id="parent_name" name="parent_name" required>
                </div>
                <div class="form-group">
                    <label for="email">Email</label>
                    <input type="email" id="email" name="email" required>
                </div>
                <div class="form-group">
                    <label for="password">Password</label>
                    <input type="password" id="password" name="password" required>
                </div>
                <div class="form-group">
                    <label for="mobile">Mobile</label>
                    <input type="tel" id="mobile" name="mobile" required>
                </div>
                <button type="submit" class="btn-primary">Register</button>
            </form>
            <p class="login-link">Already have an account? <a href="/login">Sign In</a></p>
        </div>
    </div>
</body>
</html>''',

    f'{templates_dir}/dashboard.html': '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard - Guardian Eyes</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='dashboard.css') }}">
</head>
<body>
    <nav class="navbar">
        <div class="nav-brand">Guardian Eyes</div>
        <div class="nav-links">
            <a href="/dashboard" class="active">Dashboard</a>
            <a href="/camera-management">Cameras</a>
            <a href="/video-input">Video Analysis</a>
            <a href="/alerts">Alerts</a>
            <a href="/settings">Settings</a>
            <a href="/logout">Logout</a>
        </div>
    </nav>
    <main class="dashboard-content">
        <h1>Welcome, {{ user.parent_name }}!</h1>
        <div class="stats-grid">
            <div class="stat-card">
                <h3>Active Cameras</h3>
                <p class="stat-value">0</p>
            </div>
            <div class="stat-card">
                <h3>Alerts Today</h3>
                <p class="stat-value">0</p>
            </div>
            <div class="stat-card">
                <h3>Videos Analyzed</h3>
                <p class="stat-value">0</p>
            </div>
        </div>
    </main>
</body>
</html>''',

    f'{templates_dir}/alerts.html': '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Alerts - Guardian Eyes</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='alerts.css') }}">
</head>
<body>
    <nav class="navbar">
        <div class="nav-brand">Guardian Eyes</div>
        <div class="nav-links">
            <a href="/dashboard">Dashboard</a>
            <a href="/camera-management">Cameras</a>
            <a href="/video-input">Video Analysis</a>
            <a href="/alerts" class="active">Alerts</a>
            <a href="/settings">Settings</a>
            <a href="/logout">Logout</a>
        </div>
    </nav>
    <main class="alerts-content">
        <h1>Alerts</h1>
        <div class="alerts-list">
            {% if alerts %}
                {% for alert in alerts %}
                <div class="alert-item {{ alert.severity }}">
                    <div class="alert-info">
                        <h4>{{ alert.title }}</h4>
                        <p>{{ alert.message }}</p>
                        <span class="alert-time">{{ alert.timestamp }}</span>
                    </div>
                </div>
                {% endfor %}
            {% else %}
                <p class="no-alerts">No alerts at this time</p>
            {% endif %}
        </div>
    </main>
</body>
</html>''',

    f'{templates_dir}/camera_management.html': '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Camera Management - Guardian Eyes</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='camera_management.css') }}">
</head>
<body>
    <nav class="navbar">
        <div class="nav-brand">Guardian Eyes</div>
        <div class="nav-links">
            <a href="/dashboard">Dashboard</a>
            <a href="/camera-management" class="active">Cameras</a>
            <a href="/video-input">Video Analysis</a>
            <a href="/alerts">Alerts</a>
            <a href="/settings">Settings</a>
            <a href="/logout">Logout</a>
        </div>
    </nav>
    <main class="camera-content">
        <div class="header">
            <h1>Camera Management</h1>
            <a href="/add-camera" class="btn-add">Add Camera</a>
        </div>
        <div class="camera-grid">
            {% if cameras %}
                {% for camera in cameras %}
                <div class="camera-card">
                    <h3>{{ camera.name }}</h3>
                    <p class="status {{ camera.status }}">{{ camera.status }}</p>
                    <button class="btn-delete" onclick="deleteCamera('{{ camera.id }}')">Delete</button>
                </div>
                {% endfor %}
            {% else %}
                <p class="no-cameras">No cameras added yet. <a href="/add-camera">Add your first camera</a></p>
            {% endif %}
        </div>
    </main>
    <script>
        function deleteCamera(cameraId) {
            if (confirm('Are you sure you want to delete this camera?')) {
                fetch('/delete-camera/' + cameraId, { method: 'DELETE' })
                    .then(() => location.reload());
            }
        }
    </script>
</body>
</html>''',

    f'{templates_dir}/settings.html': '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Settings - Guardian Eyes</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='settings.css') }}">
</head>
<body>
    <nav class="navbar">
        <div class="nav-brand">Guardian Eyes</div>
        <div class="nav-links">
            <a href="/dashboard">Dashboard</a>
            <a href="/camera-management">Cameras</a>
            <a href="/video-input">Video Analysis</a>
            <a href="/alerts">Alerts</a>
            <a href="/settings" class="active">Settings</a>
            <a href="/logout">Logout</a>
        </div>
    </nav>
    <main class="settings-content">
        <h1>Settings</h1>
        <form action="/update-settings" method="POST">
            <div class="form-group">
                <label for="parent_name">Parent Name</label>
                <input type="text" id="parent_name" name="parent_name" value="{{ user.parent_name }}">
            </div>
            <div class="form-group">
                <label for="email">Email</label>
                <input type="email" id="email" name="email" value="{{ user.email }}">
            </div>
            <div class="form-group">
                <label for="mobile">Mobile</label>
                <input type="tel" id="mobile" name="mobile" value="{{ user.mobile }}">
            </div>
            <button type="submit" class="btn-primary">Save Changes</button>
        </form>
    </main>
</body>
</html>''',

    f'{templates_dir}/video_input.html': '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Video Analysis - Guardian Eyes</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='video_input.css') }}">
</head>
<body>
    <nav class="navbar">
        <div class="nav-brand">Guardian Eyes</div>
        <div class="nav-links">
            <a href="/dashboard">Dashboard</a>
            <a href="/camera-management">Cameras</a>
            <a href="/video-input" class="active">Video Analysis</a>
            <a href="/alerts">Alerts</a>
            <a href="/settings">Settings</a>
            <a href="/logout">Logout</a>
        </div>
    </nav>
    <main class="video-content">
        <h1>Video Analysis</h1>
        <div class="upload-section">
            <form action="/upload-video" method="POST" enctype="multipart/form-data">
                <div class="form-group">
                    <label for="video">Upload Video</label>
                    <input type="file" id="video" name="video" accept="video/*" required>
                </div>
                <button type="submit" class="btn-primary">Analyze Video</button>
            </form>
            <div class="or-divider">OR</div>
            <form action="/upload-video-url" method="POST">
                <div class="form-group">
                    <label for="video_url">Video URL</label>
                    <input type="url" id="video_url" name="video_url" placeholder="https://example.com/video.mp4">
                </div>
                <button type="submit" class="btn-secondary">Analyze URL</button>
            </form>
        </div>
    </main>
</body>
</html>''',

    f'{templates_dir}/video_results.html': '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Analysis Results - Guardian Eyes</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='video_results.css') }}">
</head>
<body>
    <nav class="navbar">
        <div class="nav-brand">Guardian Eyes</div>
        <div class="nav-links">
            <a href="/dashboard">Dashboard</a>
            <a href="/camera-management">Cameras</a>
            <a href="/video-input">Video Analysis</a>
            <a href="/alerts">Alerts</a>
            <a href="/settings">Settings</a>
            <a href="/logout">Logout</a>
        </div>
    </nav>
    <main class="results-content">
        <h1>Analysis Results</h1>
        <div class="results-card">
            <div class="status-indicator safe">
                <span class="status-icon">&#10004;</span>
                <h2>No Issues Detected</h2>
            </div>
            <div class="result-details">
                <p>Video ID: {{ video_id }}</p>
                <p>The video has been analyzed and no safety concerns were detected.</p>
            </div>
            <a href="/video-input" class="btn-primary">Analyze Another Video</a>
        </div>
    </main>
</body>
</html>''',

    # CSS Files
    f'{static_dir}/login.css': '''* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: Arial, sans-serif;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
}

.login-container {
    width: 100%;
    max-width: 400px;
    padding: 20px;
}

.login-box {
    background: white;
    padding: 40px;
    border-radius: 12px;
    box-shadow: 0 10px 40px rgba(0,0,0,0.2);
}

.login-box h1 {
    color: #333;
    margin-bottom: 10px;
    text-align: center;
}

.subtitle {
    color: #666;
    text-align: center;
    margin-bottom: 30px;
}

.form-group {
    margin-bottom: 20px;
}

.form-group label {
    display: block;
    margin-bottom: 8px;
    color: #333;
    font-weight: 500;
}

.form-group input {
    width: 100%;
    padding: 12px;
    border: 2px solid #e0e0e0;
    border-radius: 8px;
    font-size: 16px;
    transition: border-color 0.3s;
}

.form-group input:focus {
    outline: none;
    border-color: #667eea;
}

.btn-primary {
    width: 100%;
    padding: 14px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 16px;
    font-weight: 600;
    cursor: pointer;
    transition: transform 0.2s;
}

.btn-primary:hover {
    transform: translateY(-2px);
}

.register-link {
    text-align: center;
    margin-top: 20px;
    color: #666;
}

.register-link a {
    color: #667eea;
    text-decoration: none;
    font-weight: 600;
}''',

    f'{static_dir}/register.css': '''* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: Arial, sans-serif;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
}

.register-container {
    width: 100%;
    max-width: 450px;
    padding: 20px;
}

.register-box {
    background: white;
    padding: 40px;
    border-radius: 12px;
    box-shadow: 0 10px 40px rgba(0,0,0,0.2);
}

.register-box h1 {
    color: #333;
    margin-bottom: 30px;
    text-align: center;
}

.form-group {
    margin-bottom: 20px;
}

.form-group label {
    display: block;
    margin-bottom: 8px;
    color: #333;
    font-weight: 500;
}

.form-group input {
    width: 100%;
    padding: 12px;
    border: 2px solid #e0e0e0;
    border-radius: 8px;
    font-size: 16px;
    transition: border-color 0.3s;
}

.form-group input:focus {
    outline: none;
    border-color: #667eea;
}

.btn-primary {
    width: 100%;
    padding: 14px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 16px;
    font-weight: 600;
    cursor: pointer;
    transition: transform 0.2s;
}

.btn-primary:hover {
    transform: translateY(-2px);
}

.login-link {
    text-align: center;
    margin-top: 20px;
    color: #666;
}

.login-link a {
    color: #667eea;
    text-decoration: none;
    font-weight: 600;
}''',

    f'{static_dir}/dashboard.css': '''* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: Arial, sans-serif;
    background: #f5f5f5;
    min-height: 100vh;
}

.navbar {
    background: white;
    padding: 15px 40px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.nav-brand {
    font-size: 1.5rem;
    font-weight: bold;
    color: #667eea;
}

.nav-links a {
    margin-left: 30px;
    color: #666;
    text-decoration: none;
    font-weight: 500;
    transition: color 0.3s;
}

.nav-links a:hover,
.nav-links a.active {
    color: #667eea;
}

.dashboard-content {
    padding: 40px;
    max-width: 1200px;
    margin: 0 auto;
}

.dashboard-content h1 {
    margin-bottom: 30px;
    color: #333;
}

.stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 20px;
}

.stat-card {
    background: white;
    padding: 30px;
    border-radius: 12px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    text-align: center;
}

.stat-card h3 {
    color: #666;
    margin-bottom: 15px;
    font-size: 1rem;
}

.stat-value {
    font-size: 2.5rem;
    font-weight: bold;
    color: #667eea;
}''',

    f'{static_dir}/alerts.css': '''* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: Arial, sans-serif;
    background: #f5f5f5;
    min-height: 100vh;
}

.navbar {
    background: white;
    padding: 15px 40px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.nav-brand {
    font-size: 1.5rem;
    font-weight: bold;
    color: #667eea;
}

.nav-links a {
    margin-left: 30px;
    color: #666;
    text-decoration: none;
    font-weight: 500;
    transition: color 0.3s;
}

.nav-links a:hover,
.nav-links a.active {
    color: #667eea;
}

.alerts-content {
    padding: 40px;
    max-width: 1200px;
    margin: 0 auto;
}

.alerts-content h1 {
    margin-bottom: 30px;
    color: #333;
}

.alerts-list {
    display: flex;
    flex-direction: column;
    gap: 15px;
}

.alert-item {
    background: white;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    border-left: 4px solid #667eea;
}

.alert-item.warning {
    border-left-color: #f39c12;
}

.alert-item.critical {
    border-left-color: #e74c3c;
}

.alert-item h4 {
    color: #333;
    margin-bottom: 8px;
}

.alert-item p {
    color: #666;
    margin-bottom: 8px;
}

.alert-time {
    color: #999;
    font-size: 0.9rem;
}

.no-alerts {
    text-align: center;
    color: #666;
    padding: 40px;
}''',

    f'{static_dir}/camera_management.css': '''* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: Arial, sans-serif;
    background: #f5f5f5;
    min-height: 100vh;
}

.navbar {
    background: white;
    padding: 15px 40px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.nav-brand {
    font-size: 1.5rem;
    font-weight: bold;
    color: #667eea;
}

.nav-links a {
    margin-left: 30px;
    color: #666;
    text-decoration: none;
    font-weight: 500;
    transition: color 0.3s;
}

.nav-links a:hover,
.nav-links a.active {
    color: #667eea;
}

.camera-content {
    padding: 40px;
    max-width: 1200px;
    margin: 0 auto;
}

.header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 30px;
}

.header h1 {
    color: #333;
}

.btn-add {
    padding: 12px 24px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    text-decoration: none;
    border-radius: 8px;
    font-weight: 600;
    transition: transform 0.2s;
}

.btn-add:hover {
    transform: translateY(-2px);
}

.camera-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 20px;
}

.camera-card {
    background: white;
    padding: 25px;
    border-radius: 12px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
}

.camera-card h3 {
    color: #333;
    margin-bottom: 10px;
}

.status {
    display: inline-block;
    padding: 5px 12px;
    border-radius: 20px;
    font-size: 0.85rem;
    font-weight: 500;
    margin-bottom: 15px;
}

.status.online {
    background: #d4edda;
    color: #155724;
}

.status.offline {
    background: #f8d7da;
    color: #721c24;
}

.btn-delete {
    padding: 8px 16px;
    background: #e74c3c;
    color: white;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    transition: background 0.3s;
}

.btn-delete:hover {
    background: #c0392b;
}

.no-cameras {
    text-align: center;
    color: #666;
    padding: 60px;
    grid-column: 1 / -1;
}

.no-cameras a {
    color: #667eea;
    text-decoration: none;
    font-weight: 600;
}''',

    f'{static_dir}/settings.css': '''* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: Arial, sans-serif;
    background: #f5f5f5;
    min-height: 100vh;
}

.navbar {
    background: white;
    padding: 15px 40px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.nav-brand {
    font-size: 1.5rem;
    font-weight: bold;
    color: #667eea;
}

.nav-links a {
    margin-left: 30px;
    color: #666;
    text-decoration: none;
    font-weight: 500;
    transition: color 0.3s;
}

.nav-links a:hover,
.nav-links a.active {
    color: #667eea;
}

.settings-content {
    padding: 40px;
    max-width: 600px;
    margin: 0 auto;
}

.settings-content h1 {
    margin-bottom: 30px;
    color: #333;
}

.form-group {
    margin-bottom: 25px;
}

.form-group label {
    display: block;
    margin-bottom: 10px;
    color: #333;
    font-weight: 500;
}

.form-group input {
    width: 100%;
    padding: 12px;
    border: 2px solid #e0e0e0;
    border-radius: 8px;
    font-size: 16px;
    transition: border-color 0.3s;
}

.form-group input:focus {
    outline: none;
    border-color: #667eea;
}

.btn-primary {
    padding: 14px 32px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 16px;
    font-weight: 600;
    cursor: pointer;
    transition: transform 0.2s;
}

.btn-primary:hover {
    transform: translateY(-2px);
}''',

    f'{static_dir}/video_input.css': '''* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: Arial, sans-serif;
    background: #f5f5f5;
    min-height: 100vh;
}

.navbar {
    background: white;
    padding: 15px 40px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.nav-brand {
    font-size: 1.5rem;
    font-weight: bold;
    color: #667eea;
}

.nav-links a {
    margin-left: 30px;
    color: #666;
    text-decoration: none;
    font-weight: 500;
    transition: color 0.3s;
}

.nav-links a:hover,
.nav-links a.active {
    color: #667eea;
}

.video-content {
    padding: 40px;
    max-width: 600px;
    margin: 0 auto;
}

.video-content h1 {
    margin-bottom: 30px;
    color: #333;
}

.upload-section {
    background: white;
    padding: 40px;
    border-radius: 12px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
}

.form-group {
    margin-bottom: 25px;
}

.form-group label {
    display: block;
    margin-bottom: 10px;
    color: #333;
    font-weight: 500;
}

.form-group input[type="file"],
.form-group input[type="url"] {
    width: 100%;
    padding: 12px;
    border: 2px solid #e0e0e0;
    border-radius: 8px;
    font-size: 16px;
}

.btn-primary,
.btn-secondary {
    width: 100%;
    padding: 14px;
    border: none;
    border-radius: 8px;
    font-size: 16px;
    font-weight: 600;
    cursor: pointer;
    transition: transform 0.2s;
}

.btn-primary {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
}

.btn-secondary {
    background: #f5f5f5;
    color: #667eea;
    border: 2px solid #667eea;
}

.btn-primary:hover,
    .btn-secondary:hover {
    transform: translateY(-2px);
}

.or-divider {
    text-align: center;
    margin: 30px 0;
    color: #666;
    font-weight: 500;
    position: relative;
}

.or-divider::before,
.or-divider::after {
    content: '';
    position: absolute;
    top: 50%;
    width: 40%;
    height: 1px;
    background: #e0e0e0;
}

.or-divider::before {
    left: 0;
}

.or-divider::after {
    right: 0;
}''',

    f'{static_dir}/video_results.css': '''* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: Arial, sans-serif;
    background: #f5f5f5;
    min-height: 100vh;
}

.navbar {
    background: white;
    padding: 15px 40px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.nav-brand {
    font-size: 1.5rem;
    font-weight: bold;
    color: #667eea;
}

.nav-links a {
    margin-left: 30px;
    color: #666;
    text-decoration: none;
    font-weight: 500;
    transition: color 0.3s;
}

.nav-links a:hover,
.nav-links a.active {
    color: #667eea;
}

.results-content {
    padding: 40px;
    max-width: 800px;
    margin: 0 auto;
}

.results-content h1 {
    margin-bottom: 30px;
    color: #333;
}

.results-card {
    background: white;
    padding: 40px;
    border-radius: 12px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    text-align: center;
}

.status-indicator {
    margin-bottom: 30px;
}

.status-indicator.safe {
    color: #27ae60;
}

.status-indicator.warning {
    color: #f39c12;
}

.status-indicator.critical {
    color: #e74c3c;
}

.status-icon {
    font-size: 4rem;
    display: block;
    margin-bottom: 15px;
}

.status-indicator h2 {
    font-size: 1.8rem;
}

.result-details {
    margin-bottom: 30px;
}

.result-details p {
    color: #666;
    margin-bottom: 10px;
}

.btn-primary {
    padding: 14px 32px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 16px;
    font-weight: 600;
    cursor: pointer;
    text-decoration: none;
    display: inline-block;
    transition: transform 0.2s;
}

.btn-primary:hover {
    transform: translateY(-2px);
}''',

    f'{static_dir}/add_camera.css': '''* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: Arial, sans-serif;
    background: #f5f5f5;
    min-height: 100vh;
}

.navbar {
    background: white;
    padding: 15px 40px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.nav-brand {
    font-size: 1.5rem;
    font-weight: bold;
    color: #667eea;
}

.nav-links a {
    margin-left: 30px;
    color: #666;
    text-decoration: none;
    font-weight: 500;
    transition: color 0.3s;
}

.nav-links a:hover,
.nav-links a.active {
    color: #667eea;
}

.add-camera-content {
    padding: 40px;
    max-width: 600px;
    margin: 0 auto;
}

.add-camera-content h1 {
    margin-bottom: 30px;
    color: #333;
}

.form-group {
    margin-bottom: 25px;
}

.form-group label {
    display: block;
    margin-bottom: 10px;
    color: #333;
    font-weight: 500;
}

.form-group input,
.form-group select {
    width: 100%;
    padding: 12px;
    border: 2px solid #e0e0e0;
    border-radius: 8px;
    font-size: 16px;
    transition: border-color 0.3s;
}

.form-group input:focus,
.form-group select:focus {
    outline: none;
    border-color: #667eea;
}

.btn-primary {
    padding: 14px 32px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 16px;
    font-weight: 600;
    cursor: pointer;
    transition: transform 0.2s;
}

.btn-primary:hover {
    transform: translateY(-2px);
}
''',
}

for filepath, content in files_to_create.items():
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'Created: {filepath}')

print('\\nAll files created successfully!')

