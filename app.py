from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

app = Flask(__name__)

# Configure SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///family_points.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database model for family members
class FamilyMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    points = db.Column(db.Integer, default=0)
    completed_tasks = db.Column(db.Text, default='[]')
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)

    def get_completed_tasks(self):
        """Convert JSON string back to Python list"""
        return json.loads(self.completed_tasks)

    def set_completed_tasks(self, tasks_list):
        """Convert Python list to JSON string for storage"""
        self.completed_tasks = json.dumps(tasks_list)

    def add_task(self, task_name):
        """Add a task to the completed tasks list"""
        tasks = self.get_completed_tasks()
        if task_name not in tasks: # Avoids duplicates
            tasks = list(tasks)
            tasks.append(task_name)
            self.set_completed_tasks(tasks)

    def to_dict(self):
        return {
            'name': self.name,
            'points': self.points,
            'completed_tasks': self.completed_tasks,
            'last_updated': self.last_updated.isoformat()
        }

# Database model for tasks
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    # quantity = db.Column(db.ARRAY(Integer), default=[1,1,1])
    # subtasks = db.Column(db.ARRAY(String), default=[])

# Create tables before first request
with app.app_context():
    db.create_all()

def member_to_json(member):
    """Helper to convert member to JSON"""
    return {
        'name': member.name,
        'points': member.points,
        'completed_tasks': member.get_completed_tasks(),
        'last_updated': member.last_updated.isoformat()
    }

@app.route('/')
def home():
    return "Family Points API is running! 🎉"


# Accessing family member information
@app.route('/<name>', methods=['GET', 'POST', 'PUT'])
def access_member_data(name):
    member = FamilyMember.query.filter_by(name=name).first()

    if not member:
        # Create new member
        member = FamilyMember(name=name, points=0)
        db.session.add(member)
        db.session.commit()
        return jsonify(member_to_json(member))

    if request.method == 'GET':
        return jsonify({
            'name': member.name,
            'points': member.points,
            'completed_tasks': member.get_completed_tasks(),
            'last_updated': member.last_updated.isoformat()
        })

    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    points_to_update = data.get('points')
    task_to_update = data.get('task')

    if request.method == 'POST':
        member.points += points_to_update
        member.add_task(task_to_update)
    elif request.method == 'PUT':
        member.points = points_to_update
        member.set_completed_tasks(task_to_update)

    member.last_updated = datetime.utcnow()
    db.session.commit()
    return jsonify(member_to_json(member))


# Getting the leaderboard
@app.route('/leaderboard', methods=['GET'])
def leaderboard():
    members = FamilyMember.query.order_by(FamilyMember.points.desc()).all()
    return jsonify({
        'leaderboard': [member.to_dict() for member in members]
    })

# Removing a family member
@app.route('/<name>/delete', methods=['DELETE'])
def reset_member(name):
    """Delete a family member (for testing)"""
    member = FamilyMember.query.filter_by(name=name).first()

    if member:
        db.session.delete(member)
        db.session.commit()
        return jsonify({'message': f'{name} has been deleted'})

    return jsonify({'message': f'{name} not found'}), 404


if __name__ == '__main__':
    # For local development
    app.run(debug=True, host='0.0.0.0', port=5000)
