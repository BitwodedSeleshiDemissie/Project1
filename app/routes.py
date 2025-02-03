from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from . import db, login_manager
from app.models import User, Trip, Booking, Question, Answer  # Import Answer here as needed
from app.forms import LoginForm, RegistrationForm, TripForm, BookingForm, QuestionForm
from app.forms import AnswerForm  # Add this line to import AnswerForm
from datetime import datetime
from datetime import timezone
from sqlalchemy.sql import func
from app.forms import AnswerForm
from sqlalchemy import func 




def init_app(app):
    @app.route('/')
    def home():
        print(f"User authenticated: {current_user.is_authenticated}")  # Debug
        if current_user.is_authenticated:
            print(f"User role: {current_user.role}")  # Debug
            # Use the ROUTE FUNCTION NAMES, not template paths!
            if current_user.role == 'coordinator':
                return redirect(url_for('coordinator_dashboard'))
            else:
                return redirect(url_for('traveler_dashboard'))
        return render_template('index.html')  # This line changed from redirect
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(username=form.username.data).first()
            if user and check_password_hash(user.password, form.password.data):  # Secure password check
                login_user(user, remember=True)
                next_page = request.args.get('next')
                return redirect(next_page or url_for('coordinator_dashboard' if user.role == 'coordinator' else 'traveler_dashboard'))
            flash('Login failed. Check username and password.', 'danger')
        return render_template('auth/login.html', form=form)

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        form = RegistrationForm()
        if form.validate_on_submit():
            hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256')
            user = User(username=form.username.data, password=hashed_password, role=form.role.data)
            try:
                db.session.add(user)
                db.session.commit()
                flash('Registration successful!', 'success')
                return redirect(url_for('login'))
            except Exception as e:
                db.session.rollback()
                flash(f'Error during registration: {e}', 'danger')
        return render_template('auth/register.html', form=form)

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('login'))

    @app.route('/coordinator/dashboard')
    @login_required
    def coordinator_dashboard():
        if current_user.role != 'coordinator':
            return redirect(url_for('traveler_dashboard'))
        
        # Fetch trips created by the coordinator
        trips = Trip.query.filter_by(coordinator_id=current_user.id).all()
        
        # Fetch all unanswered questions for the coordinator's trips
        inquiries = Question.query.join(Trip).filter(
            Trip.coordinator_id == current_user.id,
            Question.answer == None  # Only unanswered questions
        ).all()
        
        return render_template('coordinator/dashboard.html', trips=trips, inquiries=inquiries)

    @app.route('/coordinator/trip/create', methods=['GET', 'POST'])
    @login_required
    def create_trip():
        form = TripForm()

        if form.validate_on_submit():
            # Check if this is an edit operation (form has an ID)
            if form.id.data:
                trip = Trip.query.get(form.id.data)
                if trip.coordinator_id != current_user.id:
                    flash('You are not authorized to edit this trip.', 'danger')
                    return redirect(url_for('coordinator_dashboard'))
            else:
                # Create a new trip
                trip = Trip(coordinator_id=current_user.id)

            # Populate the trip object with form data
            form.populate_obj(trip)

            # Check if the "Publish" button was clicked
            if 'publish' in request.form:
                trip.status = 'published'
            else:
                trip.status = 'draft'  # Default to draft when saving

            try:
                db.session.add(trip)
                db.session.commit()
                flash('Trip saved successfully!', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Error saving trip: {e}', 'danger')

            return redirect(url_for('coordinator_dashboard'))

        return render_template('coordinator/create_trip.html', form=form, is_edit=False)

    @app.route('/coordinator/trip/<int:trip_id>/publish', methods=['POST'])
    @login_required
    def publish_trip(trip_id):
        trip = Trip.query.get_or_404(trip_id)
        if trip.coordinator_id == current_user.id:
            trip.status = 'published'
            try:
                db.session.commit()
                flash('Trip published successfully!', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Error publishing trip: {e}', 'danger')
        else:
            flash('You are not authorized to publish this trip.', 'danger')
        return redirect(url_for('coordinator_dashboard'))

    @app.route('/traveler/dashboard')
    @login_required
    def traveler_dashboard():
        if current_user.role != 'traveler':
            return redirect(url_for('coordinator_dashboard'))

        # Fetch booked and available trips with budget data
        booked_trips = Trip.query.join(Booking).filter(
            Booking.traveler_id == current_user.id,
            Trip.start_date > datetime.utcnow().date(),
            Trip.status == 'published'
        ).all()

        available_trips = Trip.query.filter(
            Trip.status == 'published',
            Trip.start_date > datetime.utcnow().date(),
            ~Trip.bookings.any(Booking.traveler_id == current_user.id)
        ).outerjoin(Booking).group_by(Trip.id).having(
            func.count(Booking.id) < Trip.max_participants
        ).all()

        # Fetch all questions asked by the traveler along with their answers
        inquiries = Question.query.options(db.joinedload(Question.answer)).filter_by(traveler_id=current_user.id).all()

        return render_template(
            'traveler/dashboard.html',
            booked_trips=booked_trips,
            available_trips=available_trips,
            inquiries=inquiries
        )
    @app.route('/book_trip/<int:trip_id>', methods=['GET', 'POST'])
    @login_required
    def book_trip(trip_id):
        trip = Trip.query.get_or_404(trip_id)

        # Check if the trip is upcoming and has available slots
        if not trip.is_upcoming():
            flash('You cannot book a trip that has already occurred.', 'danger')
            return redirect(url_for('home'))  # Adjust 'home' as per your route name

        if not trip.has_available_slots():
            flash('This trip is fully booked.', 'danger')
            return redirect(url_for('home'))  # Adjust 'home' as per your route name

        # Check for conflicting bookings
        if trip.is_conflicting_with_existing_bookings(current_user.id):
            flash('You already have a booking that conflicts with this trip.', 'danger')
            return redirect(url_for('home'))  # Adjust 'home' as per your route name

        form = BookingForm()

        if form.validate_on_submit():
            # Create a new booking
            booking = Booking(traveler_id=current_user.id, trip_id=trip.id)
            db.session.add(booking)
            db.session.commit()
            flash('You have successfully booked the trip!', 'success')
            return redirect(url_for('home'))  # Adjust 'home' as per your route name

        return render_template('traveler/book_trip.html', form=form, trip=trip)

    @app.route('/traveler/trip/<int:trip_id>/ask', methods=['GET', 'POST'])
    @login_required
    def ask_question(trip_id):
        form = QuestionForm()
        trip = Trip.query.get_or_404(trip_id)
        
        if form.validate_on_submit():
            question = Question(
                content=form.content.data,
                trip_id=trip.id,
                traveler_id=current_user.id
            )
            try:
                db.session.add(question)
                db.session.commit()
                flash('Your question has been submitted!', 'success')
                return redirect(url_for('traveler_dashboard'))
            except Exception as e:
                db.session.rollback()
                flash(f'Error submitting question: {e}', 'danger')
        
        return render_template('traveler/ask_question.html', form=form, trip=trip)

    @app.route('/edit_trip/<int:id>', methods=['GET', 'POST'])
    @login_required
    def edit_trip(id):
        # Fetch the trip by ID from the database
        trip = Trip.query.get_or_404(id)
        
        # Ensure the current user is the coordinator of this trip
        if trip.coordinator_id != current_user.id:
            flash('You are not authorized to edit this trip.', 'danger')
            return redirect(url_for('coordinator_dashboard'))
        
        # Prevent editing if the trip is published
        if trip.status == 'published':
            flash('Published trips cannot be edited.', 'danger')
            return redirect(url_for('coordinator_dashboard'))
        
        # Create the form with prefilled data from the trip object
        form = TripForm(obj=trip)
        
        # Check if the form was submitted and is valid
        if form.validate_on_submit():
            # Update the trip with the new values from the form
            form.populate_obj(trip)
            
            # Check if the "Publish" button was clicked
            if 'publish' in request.form:
                trip.status = 'published'
            else:
                trip.status = 'draft'  # Default to draft when saving
            
            try:
                db.session.commit()  # Commit the changes to the database
                flash('Trip updated successfully!', 'success')  # Show success message
            except Exception as e:
                db.session.rollback()  # Rollback if something goes wrong
                flash(f'Error updating trip: {e}', 'danger')
            
            # Redirect back to the coordinator dashboard
            return redirect(url_for('coordinator_dashboard'))
        
        # Render the create_trip.html template with the form and trip data
        return render_template('coordinator/create_trip.html', form=form, trip=trip, is_edit=True)
    @app.route('/delete_trip/<int:trip_id>', methods=['POST'])
    def delete_trip(trip_id):
        trip = Trip.query.get_or_404(trip_id)
        if trip.status != 'draft':
            flash('Only draft trips can be deleted.', 'danger')
            return redirect(url_for('coordinator_dashboard'))
        
        db.session.delete(trip)
        db.session.commit()
        flash('Trip deleted successfully.', 'success')
        return redirect(url_for('coordinator_dashboard'))
        
    @app.route('/answer_question/<int:question_id>', methods=['GET', 'POST'])
    @login_required
    def answer_question(question_id):
        question = Question.query.get_or_404(question_id)
        form = AnswerForm()
        
        if form.validate_on_submit():
            print(f"Answer content: {form.content.data}")  # Debugging
            print(f"Question ID: {question.id}")  # Debugging
            print(f"Coordinator ID: {current_user.id}")  # Debugging

            answer = Answer(
                content=form.content.data,
                question_id=question.id,
                coordinator_id=current_user.id
            )
            try:
                db.session.add(answer)
                db.session.commit()
                flash('Answer submitted!', 'success')
                return redirect(url_for('coordinator_dashboard'))
            except Exception as e:
                db.session.rollback()
                flash(f'Error submitting answer: {e}', 'danger')
        
        return render_template('coordinator/answer_question.html', form=form, question=question)
    @app.route('/unbook_trip/<int:trip_id>', methods=['POST'])
    @login_required
    def unbook_trip(trip_id):
        # Get the trip and check if the user has a booking
        trip = Trip.query.get_or_404(trip_id)
        booking = Booking.query.filter_by(traveler_id=current_user.id, trip_id=trip.id).first()

        # Ensure the traveler has booked this trip
        if not booking:
            flash('You have not booked this trip.', 'danger')
            return redirect(url_for('traveler_dashboard'))

        try:
            db.session.delete(booking)
            db.session.commit()
            flash('Booking canceled successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error canceling booking: {e}', 'danger')

        return redirect(url_for('traveler_dashboard'))
    @app.route('/coordinator/profile')
    @login_required
    def coordinator_profile():
        if current_user.role != 'coordinator':
            return redirect(url_for('traveler_dashboard'))

        # Fetch the coordinator's personal information
        coordinator = current_user

        # Fetch trips created by the coordinator, separated into drafts and published
        draft_trips = Trip.query.filter_by(coordinator_id=current_user.id, status='draft').all()
        published_trips = Trip.query.filter_by(coordinator_id=current_user.id, status='published').all()

        # For each published trip, fetch the list of registered participants
        for trip in published_trips:
            trip.participants = Booking.query.filter_by(trip_id=trip.id).all()

        return render_template(
            'coordinator/profile.html',
            coordinator=coordinator,
            draft_trips=draft_trips,
            published_trips=published_trips
    )