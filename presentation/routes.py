from flask import render_template,url_for,flash,redirect,request,abort
from presentation import app,db
from presentation.models import User
from flask_login import login_user,logout_user,current_user,login_required
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from presentation.forms import LoginForm
from werkzeug.exceptions import NotFound

@app.route("/")
@app.route("/home",methods=["GET"])
def home():
    return render_template("home.html",title="Home Page")

@app.route('/login',methods=["GET","POST"])
def login():
    form = LoginForm()
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password,password):
            login_user(user, remember=True)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Incorrect email or password.','danger')
    return render_template('login.html',form=form)

@app.route('/logout',methods=["GET"])
def logout():
    if current_user.is_authenticated:
        logout_user()
        return redirect(url_for('home'))
    else:
        flash('You are already logged out.','info')
        return redirect(url_for('home'))
    return redirect(url_for('home'))

@app.route('/profile',methods=["GET"])
@login_required
def profile():
    name = current_user.first_name
    return render_template('profile.html',title=f'{name} Dashboard')

@app.route('/superadmin/add_course',methods=["GET","POST"])
@login_required
def add_course():
    user = current_user
    form = AddCourseForm()
    if user.account_type != 'admin':
        abort(404)
    if form.validate_on_submit():
        try:
            course_name = form.name.data
            doc_name = form.author_id.data.split()
            doctor = User.query.filter_by(first_name=doc_name[0],last_name=doc_name[1]).first_or_404()
            new_course = Course(course_name=course_name,doctor_id=doctor.id)
            db.session.add(new_course)
            db.session.commit()
            flash(f'{course_name} Course was added successfully to dr.{doctor.first_name} {doctor.last_name} courses list.','success')
        except NotFound:
            flash('No doctors assigned with this name.','danger')
    return render_template('add_course.html',title='Admin Panel',form=form)

@app.route('/superadmin/manage_courses', methods=["GET", "POST"])
@login_required
def manage_courses():
    user = current_user
    form = ManageCoursesForm()
    if user.account_type != 'admin':
        abort(404)
    courses = db.session.query(Course, User).join(User, Course.doctor_id == User.id).all()
    if form.validate_on_submit():
        course_name = form.name.data
        doctor_name = form.author_id.data.split()
        print(course_name,doctor_name)
        doctor_id = User.query.filter_by(first_name=doctor_name[0],last_name=doctor_name[1]).first()
        course = Course.query.filter_by(course_name=course_name,doctor_id=doctor_id.id).first()
        db.session.delete(course)
        db.session.commit()
    else:
        print('hehe')
    return render_template('admin_manage_courses.html', title='Admin Panel', form=form, courses=courses)

@app.route('/doctor/courses', methods=["GET", "POST"])
@login_required
def doctor_courses():
    user = current_user
    form = DoctorCoursesForm()
    if user.account_type != 'doctor':
        abort(404)
    courses = user.courses
    courses_data = []
    for course in courses:
        enrolled_students = [student.id for student in course.enrolled_students]
        course_info = f"{course.id};{course.course_name};{','.join(map(str, enrolled_students))}"
        courses_data.append(course_info)
    return render_template('doctor_courses.html', title='My Courses', form=form, courses=courses_data)
