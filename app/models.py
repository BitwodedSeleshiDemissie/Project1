from app import db, login_manager  # Ensure that login_manager is imported here
from flask_login import UserMixin
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, DateField, IntegerField, TextAreaField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length, Optional
from datetime import datetime  # Add this import to fix the datetime error





class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'coordinator' or 'traveler'
    trips = db.relationship('Trip', backref='coordinator', lazy=True)
    bookings = db.relationship('Booking', back_populates='traveler', lazy=True)  # Use back_populates instead of backref

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Trip(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    destination = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    max_participants = db.Column(db.Integer, nullable=False)
    itinerary = db.Column(db.String(1000), nullable=False)
    status = db.Column(db.String(20), nullable=False)  # 'draft' or 'published'
    coordinator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Budget fields
    transportation_budget = db.Column(db.Float, nullable=False, default=0.0)
    accommodation_budget = db.Column(db.Float, nullable=False, default=0.0)
    activities_budget = db.Column(db.Float, nullable=False, default=0.0)

    # Relationships
    bookings = db.relationship('Booking', back_populates='trip', lazy=True)
    questions = db.relationship('Question', backref='trip', lazy=True)


    def available_slots(self):
        return self.max_participants - len(self.bookings)

    def has_available_slots(self):
        return self.available_slots() > 0

    def is_conflicting_with_existing_bookings(self, traveler_id):
        booked_trips = Trip.query.join(Booking).filter(Booking.traveler_id == traveler_id).all()
        for booked_trip in booked_trips:
            if (self.start_date <= booked_trip.end_date) and (self.end_date >= booked_trip.start_date):
                return True
        return False

    def is_upcoming(self):
        return self.start_date > datetime.utcnow().date()

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    traveler_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    trip_id = db.Column(db.Integer, db.ForeignKey('trip.id'))

    # Relationships
    traveler = db.relationship('User', back_populates='bookings')  # Updated
    trip = db.relationship('Trip', back_populates='bookings')  # Updated

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(500), nullable=False)
    trip_id = db.Column(db.Integer, db.ForeignKey('trip.id'), nullable=False)
    traveler_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Relationships
    traveler = db.relationship('User', backref='questions')  # Add this line
    answer = db.relationship('Answer', backref='question', uselist=False, lazy=True)
class QuestionForm(FlaskForm):
    content = StringField('Your Question', validators=[DataRequired()])
    submit = SubmitField('Ask Question')


class Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    coordinator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    coordinator = db.relationship('User', backref='answers')  # Add this line
