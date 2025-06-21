from flask import Flask, render_template, redirect, request, session, url_for, jsonify
import sqlite3
import datetime
import json
import re
import requests 
import os
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
app.secret_key = '8286414385fcf859f44ee8fbaf9e1fab'

OPENROUTER_API_KEY= os.getenv("API_KEY")  
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

def query_openrouter_ai(prompt):
    """Query OpenRouter AI with improved response handling"""
    try:
        system_prompt = """You are an expert study planner. Create detailed study plans in this EXACT format:

PERIOD 1: Introduction and Foundation
TASK: Complete beginner course on [specific platform] - spend 2 hours daily for first week
RESOURCES: Khan Academy, Coursera Introduction course, YouTube channel "ExampleChannel"
TASK: Read chapters 1-3 of recommended textbook and take notes
RESOURCES: "Specific Book Title" by Author Name, online PDF resources, study guide websites
TASK: Join online community and introduce yourself, find study partner
RESOURCES: Reddit communities, Discord servers, Facebook groups, LinkedIn groups

PERIOD 2: Skill Development
TASK: Practice core techniques for 1 hour daily using structured exercises
RESOURCES: Practice websites, mobile apps, online simulators, tutorial videos
TASK: Complete intermediate level project or assignment
RESOURCES: Project templates, GitHub repositories, online tutorials, mentor guidance
TASK: Take progress assessment and identify weak areas
RESOURCES: Online quizzes, self-assessment tools, feedback platforms, progress trackers

Continue this exact pattern. Each PERIOD must have exactly 3 TASKs and each TASK must have very detailed RESOURCES line immediately after it."""
        
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "meta-llama/llama-3-70b-instruct",  
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,
            "max_tokens": 3000
        }
        
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        
        data = response.json()
        ai_response = data['choices'][0]['message']['content'].strip()
        print(f"AI RESPONSE DEBUG: {ai_response[:500]}...")  # Debug line
        return ai_response
        
    except Exception as e:
        print(f"OpenRouter API Error: {str(e)}")
        return f"Error: Could not generate plan - {str(e)}"
    

def get_study_plan(goal, deadline, period):
    """Generate AI study plan with better prompting"""
    today = datetime.date.today()
    try:
        end_date = datetime.datetime.strptime(deadline, "%Y-%m-%d").date()
        days_left = (end_date - today).days
    except ValueError:
        days_left = 30
    
    if period == "daily":
        total_periods = max(days_left, 1) 
        time_unit = "day"
    elif period == "weekly":
        total_periods = max((days_left // 7) + 1, 1)  
        time_unit = "week" 
    elif period == "monthly":
        total_periods = max((days_left // 30) + 1, 1)  
        time_unit = "month"
    else:
        total_periods = max((days_left // 365) + 1, 1)  
        time_unit = "year"
    
    prompt = f"""Create a {total_periods}-{time_unit} study plan to achieve: "{goal}"

Goal: {goal}
Timeline: {total_periods} {time_unit}s
Deadline: {deadline}

Create exactly {total_periods} periods. Each period must have exactly 3 tasks with resources.

Example format you MUST follow:
PERIOD 1: Getting Started with [Goal]
TASK: Specific actionable task with time commitment
RESOURCES: Specific websites, books, courses, tools
TASK: Another specific task with clear deliverables  
RESOURCES: More specific learning materials
TASK: Third practical task with measurable outcome
RESOURCES: Additional resources and tools

Make each task specific to achieving "{goal}" with real, actionable steps."""
    
    ai_response = query_openrouter_ai(prompt)  
    return ai_response


def parse_ai_response_to_timeline(ai_response, period, start_date, end_date, goal_text="your goal"):
    """Create timeline from AI response with debugging"""
    timeline = []
    
    try:
        start = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
    except ValueError:
        start = datetime.date.today()
        end = start + datetime.timedelta(days=30)
    
    extracted_tasks = extract_all_tasks_from_ai_response(ai_response)
    print(f"Extracted tasks: {extracted_tasks}")
    
    if period == "daily":
        total_days = (end - start).days + 1
        periods = total_days  
    elif period == "weekly":
        total_weeks = ((end - start).days // 7) + 1
        periods = total_weeks  
    elif period == "monthly":
        total_months = ((end.year - start.year) * 12) + (end.month - start.month) + 1
        periods = total_months 
    else:  
        periods = (end.year - start.year) + 1 
    
  
    for i in range(periods):
        period_num = i + 1
        
        if period == "daily":
            current_date = start + datetime.timedelta(days=i)
            period_date = current_date.strftime("%Y-%m-%d")
            period_label = f"Day {period_num}"
        elif period == "weekly":
            week_start = start + datetime.timedelta(weeks=i)
            week_end = min(week_start + datetime.timedelta(days=6), end)
            period_date = f"{week_start.strftime('%m/%d')} - {week_end.strftime('%m/%d')}"
            period_label = f"Week {period_num}"
        elif period == "monthly":
            target_month = start.month + i
            target_year = start.year
            while target_month > 12:
                target_month -= 12
                target_year += 1
            month_date = datetime.date(target_year, target_month, 1)
            period_date = month_date.strftime("%B %Y")
            period_label = f"Month {period_num}"
        else:  
            period_date = str(start.year + i)
            period_label = f"Year {period_num}"
        
        if isinstance(extracted_tasks, dict) and period_num in extracted_tasks:
            tasks = extracted_tasks[period_num]
            task_objects = []
            for i_task, task_text in enumerate(tasks):
                if len(task_text.strip()) > 10:
                    task_objects.append({
                        'id': f"task_{period_num}_{i_task+1}",
                        'text': task_text.strip(),
                        'completed': False
                    })
        else:
            continue
        
        timeline.append({
            'period_number': period_num,
            'period_label': period_label,
            'period_date': period_date,
            'tasks': task_objects,
            'completed': False
        })
    
    return timeline

def parse_structured_response(response_text):
    """Improved parsing that actually works"""
    periods = {}
    current_period = None
    current_tasks = []
    
    lines = response_text.split('\n')
    print(f"PARSING {len(lines)} lines")  # Debug
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
            
        period_match = re.match(r'PERIOD\s+(\d+):', line, re.IGNORECASE)
        if period_match:
            if current_period is not None and current_tasks:
                periods[current_period] = current_tasks
                print(f"Saved period {current_period} with {len(current_tasks)} tasks")
            
            current_period = int(period_match.group(1))
            current_tasks = []
            print(f"Found period {current_period}: {line}")
            i += 1
            continue
        
        task_match = re.match(r'TASK:\s*(.+)', line, re.IGNORECASE)
        if task_match and current_period is not None:
            task_text = task_match.group(1).strip()
            
            resources_text = ""
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                resource_match = re.match(r'RESOURCES:\s*(.+)', next_line, re.IGNORECASE)
                if resource_match:
                    resources_text = resource_match.group(1).strip()
                    i += 1  
            
            full_task = task_text
            if resources_text:
                full_task += f" | Resources: {resources_text}"
            
            current_tasks.append(full_task)
            print(f"Added task: {full_task[:100]}...")
        
        i += 1
    
    if current_period is not None and current_tasks:
        periods[current_period] = current_tasks
        print(f"Saved final period {current_period} with {len(current_tasks)} tasks")
    
    print(f"FINAL PARSED PERIODS: {list(periods.keys())}")
    return periods

def get_tasks_for_period(all_tasks_by_period, period_num, total_periods, goal_text="your goal"):
    """Get tasks - CHANGED: Only return AI-generated tasks, no fallbacks"""
    print(f"Getting tasks for period {period_num}")
    print(f"Available periods: {list(all_tasks_by_period.keys()) if isinstance(all_tasks_by_period, dict) else 'Not a dict'}")
    
    if isinstance(all_tasks_by_period, dict) and period_num in all_tasks_by_period:
        tasks = all_tasks_by_period[period_num]
        print(f"Found {len(tasks)} tasks for period {period_num}")
        
        task_objects = []
        for i, task_text in enumerate(tasks):
            if len(task_text.strip()) > 10:
                task_objects.append({
                    'id': f"task_{period_num}_{i+1}",
                    'text': task_text.strip(),
                    'completed': False
                })
        
        return task_objects
    
    return []
    
    print(f"Generating fallback tasks for period {period_num}")
    fallback_prompt = f"""Create 3 specific tasks for period {period_num} of {total_periods} to achieve: "{goal_text}"

Format each as:
TASK: [Specific actionable task]
RESOURCES: [Specific resources]

Make them detailed and practical for someone working toward: {goal_text}"""
    
    try:
        fallback_response = query_groq_ai_improved(fallback_prompt)
        fallback_tasks = []
        
        for line in fallback_response.split('\n'):
            if line.strip().upper().startswith('TASK:'):
                task_text = re.sub(r'^TASK:\s*', '', line.strip(), flags=re.IGNORECASE)
                if len(task_text) > 10:
                    fallback_tasks.append(task_text)
        
        if fallback_tasks:
            task_objects = []
            for i, task_text in enumerate(fallback_tasks[:3]):
                task_objects.append({
                    'id': f"task_{period_num}_{i+1}",
                    'text': task_text,
                    'completed': False
                })
            return task_objects
    except:
        pass
    
    # Final fallback
    return [{
        'id': f"task_{period_num}_1",
        'text': f"Research best practices and resources for {goal_text}",
        'completed': False
    }, {
        'id': f"task_{period_num}_2", 
        'text': f"Practice core skills needed for {goal_text} - dedicate 1-2 hours daily",
        'completed': False
    }, {
        'id': f"task_{period_num}_3",
        'text': f"Apply learned concepts through practical exercises for {goal_text}",
        'completed': False
    }]





def extract_all_tasks_from_ai_response(ai_response):
    """Extract tasks using the improved parser"""
    return parse_structured_response(ai_response)


def create_timeline_from_parsed_tasks(parsed_tasks, period, start_date, end_date, goal_text):
    """Create timeline directly from parsed tasks with fixed monthly calculation"""
    timeline = []
    
    try:
        start = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
    except ValueError:
        start = datetime.date.today()
        end = start + datetime.timedelta(days=30)
    
    for period_num in sorted(parsed_tasks.keys()):
        tasks = parsed_tasks[period_num]
        
        task_objects = []
        for i, task_text in enumerate(tasks):
            task_objects.append({
                'id': f"task_{period_num}_{i+1}",
                'text': task_text,
                'completed': False
            })
        
        if period == "daily":
            current_date = start + datetime.timedelta(days=period_num-1)
            period_date = current_date.strftime("%Y-%m-%d")
            period_label = f"Day {period_num}"
        elif period == "weekly":
            week_start = start + datetime.timedelta(weeks=period_num-1)
            week_end = min(week_start + datetime.timedelta(days=6), end)
            period_date = f"{week_start.strftime('%m/%d')} - {week_end.strftime('%m/%d')}"
            period_label = f"Week {period_num}"
        elif period == "monthly":
            target_month = start.month + (period_num - 1)
            target_year = start.year
            
            while target_month > 12:
                target_month -= 12
                target_year += 1
            
            month_date = datetime.date(target_year, target_month, 1)
            period_date = month_date.strftime("%B %Y")
            
            if target_year == start.year:
                period_label = f"Month {period_num}"
            else:
                years_passed = target_year - start.year
                month_in_year = target_month
                period_label = f"Year {years_passed + 1}, Month {month_in_year}"
        else:
            period_date = str(start.year + period_num - 1)
            period_label = f"Year {period_num}"
        
        timeline.append({
            'period_number': period_num,
            'period_label': period_label,
            'period_date': period_date,
            'tasks': task_objects,
            'completed': False
        })
    
    return timeline

def calculate_days_remaining(deadline_str):
    try:
        today = datetime.date.today()
        deadline = datetime.datetime.strptime(deadline_str, "%Y-%m-%d").date()
        return (deadline - today).days
    except:
        return 0

def save_goal_to_db(user_id, goal, deadline, period, study_plan, timeline_data=None):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    created_date = datetime.date.today().strftime("%Y-%m-%d")
    timeline_json = json.dumps(timeline_data) if timeline_data else None

    cursor.execute("""
        INSERT INTO goals (user_id, goal_text, deadline, period, study_plan, timeline_data, created_date, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, goal, deadline, period, study_plan, timeline_json, created_date, 'active'))

    goal_id = cursor.lastrowid
    conn.commit()
    conn.close() 

    return goal_id

def get_user_goals(user_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA table_info(goals)")
    columns = cursor.fetchall()
    
    cursor.execute("""
        SELECT id, goal_text, deadline, period, study_plan, timeline_data, created_date, status
        FROM goals 
        WHERE user_id = ? 
        ORDER BY created_date DESC
    """, (user_id,))
    
    goals_data = cursor.fetchall()
    conn.close()
    
    goals = []
    for goal_data in goals_data:
        try:
            goal = {
                'id': goal_data[0] if len(goal_data) > 0 else None,
                'goal_text': goal_data[1] if len(goal_data) > 1 else 'Unknown Goal',
                'deadline': goal_data[2] if len(goal_data) > 2 else '2024-12-31',
                'period': goal_data[3] if len(goal_data) > 3 else 'daily',
                'study_plan': goal_data[4] if len(goal_data) > 4 else 'No plan available',
                'timeline_data': goal_data[5] if len(goal_data) > 5 else None,
                'created_date': goal_data[6] if len(goal_data) > 6 else '2024-01-01',
                'status': goal_data[7] if len(goal_data) > 7 else 'active',
                'days_remaining': calculate_days_remaining(goal_data[2] if len(goal_data) > 2 else '2024-12-31')
            }
            
            if goal['timeline_data']:
                try:
                    goal['timeline_data'] = json.loads(goal['timeline_data'])
                except (json.JSONDecodeError, TypeError):
                    goal['timeline_data'] = None
            
            goals.append(goal)
            
        except Exception as e:
            continue
    
    return goals

def get_goal_by_id(goal_id, user_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, goal_text, deadline, period, study_plan, timeline_data, created_date, status
        FROM goals 
        WHERE id = ? AND user_id = ?
    """, (goal_id, user_id))
    
    goal_data = cursor.fetchone()
    conn.close()
    
    if goal_data:
        try:
            timeline_data = None
            if len(goal_data) > 5 and goal_data[5]:
                try:
                    timeline_data = json.loads(goal_data[5])
                except (json.JSONDecodeError, TypeError):
                    timeline_data = None
            
            goal = {
                'id': goal_data[0] if len(goal_data) > 0 else None,
                'goal_text': goal_data[1] if len(goal_data) > 1 else 'Unknown Goal',
                'deadline': goal_data[2] if len(goal_data) > 2 else '2024-12-31',
                'period': goal_data[3] if len(goal_data) > 3 else 'daily',
                'study_plan': goal_data[4] if len(goal_data) > 4 else 'No plan available',
                'timeline_data': timeline_data,
                'created_date': goal_data[6] if len(goal_data) > 6 else '2024-01-01',
                'status': goal_data[7] if len(goal_data) > 7 else 'active',
                'days_remaining': calculate_days_remaining(goal_data[2] if len(goal_data) > 2 else '2024-12-31')
            }
            return goal
            
        except Exception as e:
            return None
    
    return None

def update_goal_status(goal_id, user_id, status):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE goals 
        SET status = ? 
        WHERE id = ? AND user_id = ?
    """, (status, goal_id, user_id))
    
    conn.commit()
    conn.close()

def toggle_period_completion(goal_id, user_id, period_number):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT timeline_data FROM goals 
        WHERE id = ? AND user_id = ?
    """, (goal_id, user_id))
    
    result = cursor.fetchone()
    if result and result[0]:
        timeline_data = json.loads(result[0])
        
        for period in timeline_data:
            if period['period_number'] == period_number:
                period['completed'] = not period.get('completed', False)
                break
        
        cursor.execute("""
            UPDATE goals 
            SET timeline_data = ? 
            WHERE id = ? AND user_id = ?
        """, (json.dumps(timeline_data), goal_id, user_id))
        
        conn.commit()
    
    conn.close()

def update_task_status(goal_id, user_id, period_number, task_id, completed):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT timeline_data FROM goals 
        WHERE id = ? AND user_id = ?
    """, (goal_id, user_id))
    
    result = cursor.fetchone()
    if result and result[0]:
        timeline_data = json.loads(result[0])
        
        for period in timeline_data:
            if period['period_number'] == period_number:
                for task in period['tasks']:
                    if task['id'] == task_id:
                        task['completed'] = completed
                
                all_completed = all(task['completed'] for task in period['tasks'])
                period['completed'] = all_completed
                break
        
        cursor.execute("""
            UPDATE goals 
            SET timeline_data = ? 
            WHERE id = ? AND user_id = ?
        """, (json.dumps(timeline_data), goal_id, user_id))
        
        conn.commit()
    
    conn.close()

def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    username TEXT NOT NULL UNIQUE,
                    birthdate DATE NOT NULL,
                    password TEXT NOT NULL
                )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS goals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    goal_text TEXT NOT NULL,
                    deadline DATE NOT NULL,
                    period TEXT NOT NULL,
                    study_plan TEXT NOT NULL,
                    timeline_data TEXT,
                    created_date DATE NOT NULL,
                    status TEXT DEFAULT 'active',
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )''')
    
    cursor = c.execute('PRAGMA table_info(goals)')
    existing_columns = [column[1] for column in cursor.fetchall()]
    
    required_columns = {
        'timeline_data': 'TEXT',
        'status': 'TEXT DEFAULT "active"',
        'created_date': 'DATE'
    }
    
    for column_name, column_definition in required_columns.items():
        if column_name not in existing_columns:
            try:
                c.execute(f'ALTER TABLE goals ADD COLUMN {column_name} {column_definition}')
            except sqlite3.OperationalError:
                pass
    
    c.execute('''UPDATE goals 
                 SET status = 'active' 
                 WHERE status IS NULL''')
    
    c.execute('''UPDATE goals 
                 SET created_date = date('now') 
                 WHERE created_date IS NULL''')
    
    c.execute('''UPDATE goals 
                 SET period = 'daily' 
                 WHERE period IS NULL''')
    
    conn.commit()
    conn.close()

def update_goal_in_db(goal_id, user_id, goal_text, deadline, period):
    """Update an existing goal in the database"""
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    study_plan = get_study_plan(goal_text, deadline, period)
    
    today = datetime.date.today().strftime("%Y-%m-%d")
    timeline_data = parse_ai_response_to_timeline(study_plan, period, today, deadline, goal_text)
    timeline_json = json.dumps(timeline_data) if timeline_data else None
    
    cursor.execute("""
        UPDATE goals 
        SET goal_text = ?, deadline = ?, period = ?, study_plan = ?, timeline_data = ?
        WHERE id = ? AND user_id = ?
    """, (goal_text, deadline, period, study_plan, timeline_json, goal_id, user_id))
    
    conn.commit()
    conn.close()

def delete_goal(goal_id, user_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        DELETE FROM goals
        WHERE id = ? AND user_id = ?
    """, (goal_id, user_id))
    
    conn.commit()
    conn.close()

@app.route('/edit-goal/<int:goal_id>')
def edit_goal(goal_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    goal = get_goal_by_id(goal_id, session['user_id'])
    if not goal:
        return redirect(url_for('my_goals'))
    
    return render_template('edit_goal.html', goal=goal, username=session['username'])

@app.route('/update-goal/<int:goal_id>', methods=['POST'])
def update_goal_route(goal_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    goal_text = request.form.get('goal')
    deadline = request.form.get('deadline')
    period = request.form.get('period')
    
    if not goal_text or not deadline or not period:
        return redirect(url_for('edit_goal', goal_id=goal_id))
    
    existing_goal = get_goal_by_id(goal_id, session['user_id'])
    if not existing_goal:
        return redirect(url_for('my_goals'))
    
    update_goal_in_db(goal_id, session['user_id'], goal_text, deadline, period)
    return redirect(url_for('view_goal', goal_id=goal_id))

@app.template_filter('count_total_tasks')
def count_total_tasks(timeline):
    if not timeline:
        return 0
    total = 0
    try:
        for period in timeline:
            if isinstance(period, dict) and 'tasks' in period:
                total += len(period.get('tasks', []))
    except (TypeError, AttributeError):
        return 0
    return total

@app.template_filter('count_completed_tasks')
def count_completed_tasks(timeline):
    if not timeline:
        return 0
    completed = 0
    try:
        for period in timeline:
            if isinstance(period, dict) and 'tasks' in period:
                for task in period.get('tasks', []):
                    if isinstance(task, dict) and task.get('completed', False):
                        completed += 1
    except (TypeError, AttributeError):
        return 0
    return completed

@app.template_filter('count_completed_periods')
def count_completed_periods(timeline):
    if not timeline:
        return 0
    completed = 0
    try:
        for period in timeline:
            if isinstance(period, dict) and period.get('completed', False):
                completed += 1
    except (TypeError, AttributeError):
        return 0
    return completed

@app.route('/')
def home():
    return render_template('welcome.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/welcome')
def welcome():
    username = session.get('username')
    return render_template('welcome2.html', username=username)


@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        name = request.form['name']
        username = request.form['username']
        birthdate = request.form['birthdate']
        password = request.form['password']

        try:
            conn = sqlite3.connect('users.db')
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (name, username, birthdate, password) VALUES (?, ?, ?, ?)",
                (name, username, birthdate, password)
            )
            conn.commit()
            conn.close()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            error = "Username already exists!"

    return render_template("register.html", error=error)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        user = c.fetchone()
        conn.close()

        if user:
            session['user_id'] = user[0]
            session['fullname'] = user[1]
            session['username'] = user[2]
            session['birthdate'] = user[3]
            session['password'] = user[4]
            return redirect(url_for('profile'))
        else:
            error = "Invalid username or password."

    return render_template('login.html', error=error)

@app.route('/profile')
def profile():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    user_data = {
        'username': session.get('username', 'N/A'),
        'fullname': session.get('fullname', 'N/A'),
        'birthdate': session.get('birthdate', 'N/A'),
        'password': session.get('password', 'N/A')
    }
    
    return render_template('profile.html', **user_data)

@app.route('/main', methods=['GET', 'POST'])
def main():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    if request.method == "POST":
        goal = request.form.get("goal", "").strip()
        deadline = request.form.get("deadline", "")
        period = request.form.get("period", "")
        
        # Basic validation
        if not goal:
            return render_template('main.html', username=session['username'], 
                                 error="Please enter a goal")
        if not deadline:
            return render_template('main.html', username=session['username'], 
                                 error="Please select a deadline")
        if not period:
            return render_template('main.html', username=session['username'], 
                                 error="Please select a time period")
        
        return redirect(url_for('process_goal', goal=goal, deadline=deadline, period=period))
    
    return render_template('main.html', username=session['username'])

@app.route('/process-goal', methods=['GET', 'POST'])
def process_goal():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        goal = request.form.get("goal", "").strip()
        deadline = request.form.get("deadline", "")
        period = request.form.get("period", "")
    else:
        goal = request.args.get("goal", "").strip()
        deadline = request.args.get("deadline", "")
        period = request.args.get("period", "")
    
    if not goal or not deadline or not period:
        return redirect(url_for('main'))
    
    plan = get_study_plan(goal, deadline, period)
    
    today = datetime.date.today().strftime("%Y-%m-%d")
    timeline_data = parse_ai_response_to_timeline(plan, period, today, deadline, goal)
    
    goal_id = save_goal_to_db(session['user_id'], goal, deadline, period, plan, timeline_data)
    
    return redirect(url_for('view_goal', goal_id=goal_id))

@app.route('/my-goals')
def my_goals():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    try:
        goals = get_user_goals(session['user_id'])
        return render_template('my_goals.html', goals=goals, username=session['username'])
    except Exception as e:
        return render_template('my_goals.html', goals=[], username=session['username'], error="Error loading goals")

@app.route('/view-goal/<int:goal_id>')
def view_goal(goal_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    goal = get_goal_by_id(goal_id, session['user_id'])
    if not goal:
        return redirect(url_for('my_goals'))
    
    return render_template('view_goal.html', goal=goal, timeline=goal.get('timeline_data'), username=session['username'])

@app.route('/toggle-period/<int:goal_id>/<int:period_number>', methods=['POST'])
def toggle_period(goal_id, period_number):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    toggle_period_completion(goal_id, session['user_id'], period_number)
    return redirect(url_for('view_goal', goal_id=goal_id))

@app.route('/update-task-status', methods=['POST'])
def update_task_status_route():
    if 'username' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json()
    goal_id = data.get('goal_id')
    period_number = data.get('period_number')
    task_id = data.get('task_id')
    completed = data.get('completed', False)
    
    update_task_status(goal_id, session['user_id'], period_number, task_id, completed)
    
    return jsonify({'success': True})

@app.route('/update-goal-status/<int:goal_id>/<status>')
def update_status(goal_id, status):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    valid_statuses = ['active', 'completed', 'paused']
    if status in valid_statuses:
        update_goal_status(goal_id, session['user_id'], status)
    
    return redirect(url_for('my_goals'))

@app.route('/delete-goal/<int:goal_id>', methods=['POST'])
def delete_goal_route(goal_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    delete_goal(goal_id, session['user_id'])
    return redirect(url_for('my_goals'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route("/progress", methods=["GET", "POST"])
def progress():
    return redirect(url_for('main'))

@app.route("/studyplan")
def studyplan():
    if 'current_goal_id' in session:
        return redirect(url_for('view_goal', goal_id=session['current_goal_id']))
    return redirect(url_for('my_goals'))

@app.route('/test-ai')
def test_ai():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    test_goal = "learn Python programming"
    test_deadline = "2025-07-01"
    test_period = "weekly"
    
    plan = get_study_plan(test_goal, test_deadline, test_period)
    parsed = parse_structured_response(plan)

    
    return f"""
    <h2>AI Test Results</h2>
    <h3>Raw AI Response:</h3>
    <pre>{plan}</pre>
    <h3>Parsed Periods:</h3>
    <pre>{parsed}</pre>
    """



if __name__ == '__main__':
    init_db()
    app.run(debug=True)
