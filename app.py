from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

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
    completed_tasks = db.Column(db.ARRAY(String))
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)

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
    quantity = db.Column(db.ARRAY(Integer), default=[1,1,1])
    subtasks = db.Column(db.ARRAY(String), default=[])

# Create tables before first request
with app.app_context():
    db.create_all()


@app.route('/')
def home():
    return "Family Points API is running! 🎉"

# Getting family member information
@app.route('/points/<name>', methods=['GET'])
def get_points(name):
    member = FamilyMember.query.filter_by(name=name).first()

    if not member:
        return jsonify({
            'name': name,
            'points': 0,
            'message': 'Member not found, starting with 0 points'
        })

    return jsonify(member.to_dict())

# Adding points to a family member
@app.route('/points/<name>', methods=['POST'])
def add_points(name):
    data = request.get_json()
    points_to_add = data.get('points', 0)
    task_to_add = data.get('task')

    member = FamilyMember.query.filter_by(name=name).first()

    if not member:
        # Create new member
        member = FamilyMember(name=name, points=points_to_add, completed_tasks=completed_tasks.append(task_to_add))
        db.session.add(member)
    else:
        # Update existing member
        member.points += points_to_add
        member.completed_tasks.append(task_to_add)
        member.last_updated = datetime.utcnow()

    db.session.commit()

    return jsonify({
        'name': member.name,
        'points': member.points,
        'completed_tasks': member.completed_tasks,
        'message': 'Points updated!'
    })

# Setting points of a family member
@app.route('/points/<name>', methods=['PUT'])
def set_points(name):
    """Set points to an exact value (useful for resetting)"""
    data = request.get_json()
    new_points = data.get('points', 0)

    member = FamilyMember.query.filter_by(name=name).first()

    if not member:
        member = FamilyMember(name=name, points=new_points)
        db.session.add(member)
    else:
        member.points = new_points
        member.last_updated = datetime.utcnow()

    db.session.commit()

    return jsonify({
        'name': member.name,
        'points': member.points,
        'message': 'Points set!'
    })

# Getting the leaderboard
@app.route('/leaderboard', methods=['GET'])
def leaderboard():
    members = FamilyMember.query.order_by(FamilyMember.points.desc()).all()
    return jsonify({
        'leaderboard': [member.to_dict() for member in members]
    })

# Removing a family member
@app.route('/reset/<name>', methods=['DELETE'])
def reset_member(name):
    """Delete a family member (for testing)"""
    member = FamilyMember.query.filter_by(name=name).first()

    if member:
        db.session.delete(member)
        db.session.commit()
        return jsonify({'message': f'{name} has been reset'})

    return jsonify({'message': f'{name} not found'}), 404


if __name__ == '__main__':
    # For local development
    app.run(debug=True, host='0.0.0.0', port=5000)
