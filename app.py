from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
from flask_mail import Mail, Message
from flask_sqlalchemy import SQLAlchemy
from scraper import DAVScraper
from simple_rag import SimpleRAG
from models import db, Conversation, UploadedFile, Lead, ManualData, Event
import os
from dotenv import load_dotenv
import json
from datetime import datetime, timedelta
from googletrans import Translator
from gtts import gTTS
import tempfile
import uuid
import secrets

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = 'dav_admin_secret_key_2024'

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///davgpt.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Email configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = app.config['MAIL_USERNAME']

# Initialize extensions
db.init_app(app)
mail = Mail(app)

# Initialize systems
scraper = DAVScraper()
rag = SimpleRAG()
translator = Translator()

# Default admin
DEFAULT_ADMIN = {"username": "admin", "password": "dav2024", "email": "admin@davkoylanagar.com"}

def get_session_id():
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    return session['session_id']

def detect_and_translate(text):
    try:
        detection = translator.detect(text)
        if detection.lang == 'hi':
            translated = translator.translate(text, src='hi', dest='en')
            return translated.text, 'hi'
        return text, 'en'
    except:
        return text, 'en'

def translate_to_hindi(text):
    try:
        translated = translator.translate(text, src='en', dest='hi')
        return translated.text
    except:
        return text

def check_for_human_request(message):
    human_keywords = ['human', 'person', 'staff', 'talk to someone', 'contact', 'call', 'meet', 'व्यक्ति', 'इंसान', 'स्टाफ', 'संपर्क']
    return any(keyword in message.lower() for keyword in human_keywords)

def get_chatbot_response(message, user_lang='en'):
    try:
        if check_for_human_request(message):
            if user_lang == 'hi':
                return "मैं आपको स्कूल के स्टाफ से जोड़ सकता हूं। कृपया अपना नाम और संपर्क नंबर बताएं।", 'hi', True
            else:
                return "I can connect you with our school staff. Please provide your name and contact number.", 'en', True
        
        english_message, detected_lang = detect_and_translate(message)
        response = rag.generate_response(english_message)
        
        if detected_lang == 'hi':
            response = translate_to_hindi(response)
        
        return response, detected_lang, False
    except Exception as e:
        print(f"Error in chatbot response: {e}")
        return "I'm having trouble processing your request. Please try again.", 'en', False

@app.route('/')
def index():
    return render_template('chat.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message', '')
    if not user_message.strip():
        return jsonify({'response': 'Please ask me something about DAV Koyla Nagar school.'})
    
    bot_response, user_lang, needs_human = get_chatbot_response(user_message)
    
    # Store in session for 48 hours
    if 'chat_history' not in session:
        session['chat_history'] = []
    
    session['chat_history'].append({
        'user': user_message,
        'bot': bot_response,
        'timestamp': datetime.now().isoformat(),
        'language': user_lang
    })
    
    # Keep only last 50 messages
    if len(session['chat_history']) > 50:
        session['chat_history'] = session['chat_history'][-50:]
    
    session.permanent = True
    app.permanent_session_lifetime = timedelta(hours=48)
    
    return jsonify({
        'response': bot_response,
        'language': user_lang,
        'needs_human': needs_human
    })

@app.route('/get_chat_history', methods=['GET'])
def get_chat_history():
    return jsonify({'history': session.get('chat_history', [])})

@app.route('/clear_chat', methods=['POST'])
def clear_chat():
    session.pop('chat_history', None)
    return jsonify({'status': 'success', 'message': 'Chat history cleared'})

@app.route('/generate_lead', methods=['POST'])
def generate_lead():
    try:
        data = request.json
        name = data.get('name', '').strip()
        contact = data.get('contact', '').strip()
        query = data.get('query', '').strip()
        
        if not name or not contact:
            return jsonify({'status': 'error', 'message': 'Name and contact are required'})
        
        lead_entry = {
            'id': str(uuid.uuid4()),
            'timestamp': datetime.now().isoformat(),
            'name': name,
            'contact': contact,
            'query': query,
            'status': 'new'
        }
        
        leads = load_leads()
        leads.append(lead_entry)
        save_leads(leads)
        
        return jsonify({
            'status': 'success', 
            'message': 'Thank you! Our team will contact you soon.',
            'message_hi': 'धन्यवाद! हमारी टीम जल्द ही आपसे संपर्क करेगी।'
        })
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/upload_file', methods=['POST'])
def upload_file():
    """Handle file uploads (PDF, DOCX, TXT)"""
    try:
        if 'file' not in request.files:
            return jsonify({'status': 'error', 'message': 'No file selected'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'status': 'error', 'message': 'No file selected'})
        
        # Check file type
        allowed_extensions = {'.pdf', '.docx', '.txt'}
        file_ext = os.path.splitext(file.filename)[1].lower()
        
        if file_ext not in allowed_extensions:
            return jsonify({'status': 'error', 'message': 'Only PDF, DOCX, and TXT files are supported'})
        
        # Save file temporarily
        filename = f"upload_{uuid.uuid4()}{file_ext}"
        filepath = os.path.join('uploads', filename)
        
        # Create uploads directory if it doesn't exist
        os.makedirs('uploads', exist_ok=True)
        file.save(filepath)
        
        # Extract text from file
        text_content = extract_text_from_file(filepath, file_ext)
        
        if text_content:
            # Save to database
            uploaded_file = UploadedFile(
                filename=filename,
                original_name=file.filename,
                file_type=file_ext,
                content=text_content,
                session_id=get_session_id()
            )
            db.session.add(uploaded_file)
            db.session.commit()
            
            # Add to RAG system
            file_entry = {
                'id': str(uploaded_file.id),
                'title': f"Uploaded File: {file.filename}",
                'content': text_content,
                'category': 'uploaded_file',
                'timestamp': datetime.now().isoformat(),
                'url': 'uploaded_file',
                'filename': file.filename
            }
            
            rag.add_manual_entry(file_entry)
            
            # Clean up temporary file
            os.remove(filepath)
            
            return jsonify({
                'status': 'success', 
                'message': f'File "{file.filename}" uploaded and processed successfully!',
                'content_preview': text_content[:200] + '...' if len(text_content) > 200 else text_content
            })
        else:
            os.remove(filepath)
            return jsonify({'status': 'error', 'message': 'Could not extract text from file'})
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

def extract_text_from_file(filepath, file_ext):
    """Extract text from different file types"""
    try:
        if file_ext == '.pdf':
            import PyPDF2
            with open(filepath, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text.strip()
        
        elif file_ext == '.docx':
            from docx import Document
            doc = Document(filepath)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text.strip()
        
        elif file_ext == '.txt':
            with open(filepath, 'r', encoding='utf-8') as file:
                return file.read().strip()
    
    except Exception as e:
        print(f"Error extracting text: {e}")
        return None
@app.route('/get_holidays', methods=['POST'])
def get_holidays_for_chat():
    """Get holidays for chat queries"""
    try:
        data = request.json
        month = data.get('month')
        year = data.get('year', datetime.now().year)
        
        query = Event.query.filter_by(is_public_holiday=True)
        
        if month:
            query = query.filter(db.extract('month', Event.date) == month)
        
        query = query.filter(db.extract('year', Event.date) == year)
        
        holidays = query.all()
        
        holiday_list = []
        for holiday in holidays:
            holiday_list.append({
                'title': holiday.title,
                'date': holiday.date.strftime('%B %d, %Y'),
                'description': holiday.description or ''
            })
        
        return jsonify({'status': 'success', 'holidays': holiday_list})
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

def text_to_speech():
    try:
        data = request.json
        text = data.get('text', '')
        lang = data.get('language', 'en')
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
        
        tts_lang = 'hi' if lang == 'hi' else 'en'
        tts = gTTS(text=text, lang=tts_lang, slow=False)
        
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
        tts.save(temp_file.name)
        
        return send_file(temp_file.name, as_attachment=True, download_name='speech.mp3')
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin')
def admin_login():
    if 'admin_logged_in' in session:
        return redirect(url_for('admin_dashboard'))
    return render_template('admin_login.html')

@app.route('/admin/login', methods=['POST'])
def admin_authenticate():
    username = request.form.get('username')
    password = request.form.get('password')
    
    admins = load_admins()
    
    for admin in admins:
        if admin['username'] == username and admin['password'] == password:
            session['admin_logged_in'] = True
            session['admin_username'] = username
            return redirect(url_for('admin_dashboard'))
    
    return render_template('admin_login.html', error='Invalid credentials')

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))
    
    stats = get_system_stats()
    return render_template('admin_dashboard.html', stats=stats)

@app.route('/admin/admins')
def admin_manage():
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))
    
    admins = load_admins()
    return render_template('admin_manage.html', admins=admins)

@app.route('/admin/invite', methods=['POST'])
def admin_invite():
    if 'admin_logged_in' not in session:
        return jsonify({'status': 'error', 'message': 'Unauthorized'})
    
    try:
        data = request.json
        email = data.get('email', '').strip()
        name = data.get('name', '').strip()
        
        if not email or not name:
            return jsonify({'status': 'error', 'message': 'Email and name are required'})
        
        # Generate temporary password
        temp_password = secrets.token_urlsafe(12)
        
        # Create new admin
        new_admin = {
            'username': email.split('@')[0],
            'password': temp_password,
            'email': email,
            'name': name,
            'invited_by': session.get('admin_username'),
            'invited_at': datetime.now().isoformat(),
            'status': 'invited'
        }
        
        admins = load_admins()
        admins.append(new_admin)
        save_admins(admins)
        
        # Send invitation email
        send_invitation_email(email, name, new_admin['username'], temp_password)
        
        return jsonify({'status': 'success', 'message': f'Invitation sent to {email}'})
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/admin/data')
def admin_data():
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))
    
    manual_data = load_manual_data()
    return render_template('admin_data.html', data=manual_data)

@app.route('/admin/leads')
def admin_leads():
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))
    
    leads = load_leads()
    return render_template('admin_leads.html', leads=leads)

@app.route('/admin/add_data', methods=['POST'])
def admin_add_data():
    if 'admin_logged_in' not in session:
        return jsonify({'status': 'error', 'message': 'Unauthorized'})
    
    try:
        data = request.json
        title = data.get('title', '').strip()
        content = data.get('content', '').strip()
        category = data.get('category', 'general').strip()
        
        if not title or not content:
            return jsonify({'status': 'error', 'message': 'Title and content are required'})
        
        new_entry = {
            'id': str(uuid.uuid4()),
            'title': title,
            'content': content,
            'category': category,
            'timestamp': datetime.now().isoformat(),
            'url': 'manual_entry',
            'added_by': session.get('admin_username')
        }
        
        rag.add_manual_entry(new_entry)
        
        return jsonify({'status': 'success', 'message': 'Data added successfully'})
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/admin/update_lead', methods=['POST'])
def admin_update_lead():
    if 'admin_logged_in' not in session:
        return jsonify({'status': 'error', 'message': 'Unauthorized'})
    
    try:
        data = request.json
        lead_id = data.get('lead_id')
        status = data.get('status')
        
        leads = load_leads()
        for lead in leads:
            if lead['id'] == lead_id:
                lead['status'] = status
                lead['updated_by'] = session.get('admin_username')
                lead['updated_at'] = datetime.now().isoformat()
                break
        
        save_leads(leads)
        return jsonify({'status': 'success', 'message': 'Lead updated'})
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/admin/refresh', methods=['POST'])
def admin_refresh():
    if 'admin_logged_in' not in session:
        return jsonify({'status': 'error', 'message': 'Unauthorized'})
    
    try:
        scraper.scrape_all()
        rag.refresh_knowledge_base()
        return jsonify({'status': 'success', 'message': 'Knowledge base updated successfully'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/admin/calendar')
def admin_calendar():
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))
    
    return render_template('admin_calendar.html')

@app.route('/admin/events', methods=['GET'])
def get_events():
    if 'admin_logged_in' not in session:
        return jsonify({'status': 'error', 'message': 'Unauthorized'})
    
    try:
        month = request.args.get('month', datetime.now().month)
        year = request.args.get('year', datetime.now().year)
        
        # Get events for the month
        events = Event.query.filter(
            db.extract('month', Event.date) == month,
            db.extract('year', Event.date) == year
        ).all()
        
        events_data = []
        for event in events:
            events_data.append({
                'id': event.id,
                'title': event.title,
                'description': event.description,
                'date': event.date.isoformat(),
                'category': event.category,
                'tags': event.tags.split(',') if event.tags else [],
                'is_public_holiday': event.is_public_holiday
            })
        
        return jsonify({'status': 'success', 'events': events_data})
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/admin/add_event', methods=['POST'])
def add_event():
    if 'admin_logged_in' not in session:
        return jsonify({'status': 'error', 'message': 'Unauthorized'})
    
    try:
        data = request.json
        title = data.get('title', '').strip()
        description = data.get('description', '').strip()
        date_str = data.get('date', '')
        category = data.get('category', 'custom')
        tags = data.get('tags', '')
        
        if not title or not date_str:
            return jsonify({'status': 'error', 'message': 'Title and date are required'})
        
        # Parse date
        event_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Create event
        event = Event(
            title=title,
            description=description,
            date=event_date,
            category=category,
            tags=tags,
            created_by=session.get('admin_username', 'admin')
        )
        
        db.session.add(event)
        db.session.commit()
        
        return jsonify({'status': 'success', 'message': 'Event added successfully'})
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/admin/fetch_holidays', methods=['POST'])
def fetch_holidays():
    if 'admin_logged_in' not in session:
        return jsonify({'status': 'error', 'message': 'Unauthorized'})
    
    try:
        year = request.json.get('year', datetime.now().year)
        
        # Fetch Indian holidays (using a simple list for demo)
        indian_holidays = [
            {'date': f'{year}-01-26', 'title': 'Republic Day', 'description': 'National Holiday'},
            {'date': f'{year}-08-15', 'title': 'Independence Day', 'description': 'National Holiday'},
            {'date': f'{year}-10-02', 'title': 'Gandhi Jayanti', 'description': 'National Holiday'},
            {'date': f'{year}-12-25', 'title': 'Christmas Day', 'description': 'National Holiday'},
        ]
        
        # Add Diwali (approximate date - varies each year)
        if year == 2024:
            indian_holidays.append({'date': f'{year}-11-01', 'title': 'Diwali', 'description': 'Festival of Lights'})
        elif year == 2025:
            indian_holidays.append({'date': f'{year}-10-20', 'title': 'Diwali', 'description': 'Festival of Lights'})
        
        added_count = 0
        for holiday in indian_holidays:
            event_date = datetime.strptime(holiday['date'], '%Y-%m-%d').date()
            
            # Check if holiday already exists
            existing = Event.query.filter_by(date=event_date, is_public_holiday=True).first()
            if not existing:
                event = Event(
                    title=holiday['title'],
                    description=holiday['description'],
                    date=event_date,
                    category='holiday',
                    tags='public,national',
                    created_by='system',
                    is_public_holiday=True
                )
                db.session.add(event)
                added_count += 1
        
        db.session.commit()
        
        return jsonify({
            'status': 'success', 
            'message': f'Added {added_count} public holidays for {year}'
        })
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})
def admin_logs():
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))
    
    logs = get_conversation_logs()
    return render_template('admin_logs.html', logs=logs)

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    return redirect(url_for('index'))

def send_invitation_email(email, name, username, password):
    """Send admin invitation email"""
    try:
        msg = Message(
            'DAVGPT Admin Invitation',
            recipients=[email]
        )
        
        msg.html = f"""
        <h2>Welcome to DAVGPT Admin Panel</h2>
        <p>Hello {name},</p>
        <p>You have been invited to join the DAVGPT admin panel for DAV Koyla Nagar school.</p>
        
        <h3>Your Login Credentials:</h3>
        <p><strong>Username:</strong> {username}</p>
        <p><strong>Password:</strong> {password}</p>
        
        <p><a href="http://localhost:5000/admin" style="background: #004aad; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Login to Admin Panel</a></p>
        
        <p>Please change your password after first login.</p>
        
        <p>Best regards,<br>DAVGPT Team</p>
        """
        
        mail.send(msg)
        print(f"Invitation email sent to {email}")
    except Exception as e:
        print(f"Email error: {e}")

def load_admins():
    try:
        with open('admins.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return [DEFAULT_ADMIN]

def save_admins(admins):
    with open('admins.json', 'w') as f:
        json.dump(admins, f, indent=2)

def load_manual_data():
    return rag.manual_data

def load_leads():
    try:
        with open('leads.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_leads(leads):
    with open('leads.json', 'w') as f:
        json.dump(leads, f, indent=2)

def log_conversation(user_message, bot_response):
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'user_message': user_message,
        'bot_response': bot_response
    }
    
    try:
        if os.path.exists('conversation_logs.json'):
            with open('conversation_logs.json', 'r') as f:
                logs = json.load(f)
        else:
            logs = []
        
        logs.append(log_entry)
        
        if len(logs) > 1000:
            logs = logs[-1000:]
        
        with open('conversation_logs.json', 'w') as f:
            json.dump(logs, f, indent=2)
    except Exception as e:
        print(f"Error logging conversation: {e}")

def get_conversation_logs():
    try:
        with open('conversation_logs.json', 'r') as f:
            logs = json.load(f)
        return logs[-50:]
    except FileNotFoundError:
        return []

def get_system_stats():
    stats = {
        'total_conversations': 0,
        'knowledge_base_size': 0,
        'manual_entries': 0,
        'total_leads': 0,
        'new_leads': 0,
        'total_admins': 0,
        'last_update': 'Never'
    }
    
    try:
        if os.path.exists('conversation_logs.json'):
            with open('conversation_logs.json', 'r') as f:
                logs = json.load(f)
                stats['total_conversations'] = len(logs)
        
        if os.path.exists('knowledge_base.json'):
            with open('knowledge_base.json', 'r') as f:
                kb = json.load(f)
                stats['knowledge_base_size'] = len(kb)
            
            mod_time = os.path.getmtime('knowledge_base.json')
            stats['last_update'] = datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d %H:%M:%S')
        
        manual_data = load_manual_data()
        stats['manual_entries'] = len(manual_data)
        
        leads = load_leads()
        stats['total_leads'] = len(leads)
        stats['new_leads'] = len([l for l in leads if l.get('status') == 'new'])
        
        admins = load_admins()
        stats['total_admins'] = len(admins)
    
    except Exception as e:
        print(f"Error getting stats: {e}")
    
    return stats

# Initialize database on startup
with app.app_context():
    db.create_all()
    print("📊 Database initialized")

if __name__ == '__main__':
    if not os.path.exists('knowledge_base.json'):
        print("Running initial scrape...")
        scraper.scrape_all()
        rag.load_data()
    
    print("🚀 D.A.V GPT starting on http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
