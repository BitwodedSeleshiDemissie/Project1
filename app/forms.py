from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, DateField, IntegerField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo, Optional, ValidationError

from datetime import datetime

# Define AnswerForm directly here instead of dynamically
class AnswerForm(FlaskForm):
    content = TextAreaField('Your Answer', validators=[DataRequired()])
    submit = SubmitField('Submit Answer')

# Forms for various actions
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Role', choices=[('coordinator', 'Coordinator'), ('traveler', 'Traveler')], validators=[DataRequired()])
    submit = SubmitField('Register')
class TripForm(FlaskForm):
    # Hidden field for trip ID (used during editing)
    id = IntegerField('ID', validators=[Optional()])

    # Destination field
    destination = StringField('Destination', validators=[
        DataRequired(message="Destination is required."),
        Length(max=100, message="Destination cannot exceed 100 characters.")
    ])

    # Start date field with custom validation
    start_date = DateField('Start Date', validators=[
        DataRequired(message="Start date is required.")
    ])

    # End date field
    end_date = DateField('End Date', validators=[
        DataRequired(message="End date is required.")
    ])

    # Maximum participants field
    max_participants = IntegerField('Max Participants', validators=[
        DataRequired(message="Maximum participants is required."),
    ])

    # Itinerary field
    itinerary = TextAreaField('Itinerary', validators=[
        DataRequired(message="Itinerary is required."),
        Length(max=1000, message="Itinerary cannot exceed 1000 characters.")
    ])

    # Budget fields
    transportation_budget = IntegerField('Transportation Budget', validators=[
        DataRequired(message="Transportation budget is required.")
    ])
    accommodation_budget = IntegerField('Accommodation Budget', validators=[
        DataRequired(message="Accommodation budget is required.")
    ])
    activities_budget = IntegerField('Activities Budget', validators=[
        DataRequired(message="Activities budget is required.")
    ])

    # Submit button
    submit = SubmitField('Submit')

    # Custom validator to ensure start date is not in the past
    def validate_start_date(self, field):
        if field.data < datetime.utcnow().date():
            raise ValidationError('Start date cannot be in the past.')

    # Custom validator to ensure end date is after start date
    def validate_end_date(self, field):
        if self.start_date.data and field.data < self.start_date.data:
            raise ValidationError('End date must be after the start date.')
class BookingForm(FlaskForm):
    submit = SubmitField('Book Trip')

class QuestionForm(FlaskForm):
    content = TextAreaField('Your Question', validators=[DataRequired(), Length(max=500)])
    submit = SubmitField('Ask Question')