from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required,login_user,logout_user,current_user
from flask import jsonify
from src import bcrypt,db
from src.accounts.models import User
from .forms import LoginForm, RegisterForm

accounts_bp = Blueprint("accounts", __name__)

@accounts_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    register_form = RegisterForm(request.form)
    if register_form.validate_on_submit():
        user = User(email=register_form.email.data, password=register_form.password.data)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for("index"))
    return render_template('index.html', login_form=LoginForm(), register_form=register_form,show_modal=True,form_to_show="register",form_errors=register_form.errors)


@accounts_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    login_form = LoginForm(request.form)
    if login_form.validate_on_submit():
        user = User.query.filter_by(email=login_form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, request.form["password"]):
            login_user(user)
            return redirect(url_for("index"))
        else:
           error_message = 'Invalid email or password.'
           return render_template('index.html', login_form=login_form, register_form=RegisterForm(),show_modal=True,message=error_message)
    return redirect(url_for("index"))


@accounts_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))