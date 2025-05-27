from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../supabase')))
from supabase1.clients import supabase

auth_routes = Blueprint('auth', __name__)

@auth_routes.route('/')
def hero():
    return render_template('hero.html')

@auth_routes.route('/role')
def role_selection():
    action = request.args.get('action')  # 'login' or 'signup'
    return render_template('role.html', action=action)

@auth_routes.route('/login_signup')
def login_signup():
    action = request.args.get('action')
    role = request.args.get('role')
    if action=='login':
        return redirect(url_for('auth.login',role=role))
    else: return redirect(url_for('auth.signup',role=role))

@auth_routes.route('/signup', methods=['GET', 'POST'])
def signup():
    role = request.args.get('role')

    if request.method == 'POST':
        full_name = request.form.get('full_name')
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash('Passwords do not match!', 'error')
            return redirect(request.url)

        # Check for existing user
        existing = supabase.table('users').select('*').eq('username', username).execute()
        if existing.data:
            flash('Username already exists!', 'error')
            return redirect(request.url)

        # Create user
        user_data = {
            'full_name': full_name,
            'username': username,
            'email': email,
            'password': password,
            'role': role
        }
        supabase.table('users').insert(user_data).execute()

        session['username'] = username
        session['role'] = role
        current = supabase.table('users').select('*').eq('username', username).execute()

        if role == 'title_verifier':
            return redirect(url_for('user_routes.title_applicant_dashboard',username=username))
        elif role == 'prgi_official':
            if current.data[0]['verified']:
                return redirect(url_for('official_routes.official_dashboard',username=username))
            else:
                flash('Waiting for Admin Approval...', 'error')
                return redirect(request.url)
        else:
            return redirect(url_for('auth.hero'))

    return render_template('signup.html', role=role)

@auth_routes.route('/login', methods=['GET', 'POST'])
def login():
    role = request.args.get('role')

    if request.method == 'POST':
        identifier = request.form.get('identifier')
        password = request.form.get('password')

        result = supabase.table('users').select('*').or_(
            f"username.eq.{identifier},email.eq.{identifier}"
        ).eq('role', role).execute()

        user = result.data[0] if result.data else None

        if user and user['password'] == password:
            session['username'] = user['username']
            session['role'] = role
            
            current = supabase.table('users').select('*').eq('username', identifier).execute()

            if role == 'title_verifier':
                return redirect(url_for('user_routes.title_applicant_dashboard',username=identifier))
            elif role == 'prgi_official':
                if current.data[0]['verified']:
                    return redirect(url_for('official_routes.official_dashboard',username=identifier))
                else: 
                    flash("Your Account is still not verified by the admin....", "error")
                    return redirect(request.url)
            else:
                return redirect(url_for('admin_routes.admin_dashboard'))
        else:
            flash('Invalid credentials or role mismatch.', 'error')
            return redirect(request.url)

    return render_template('login.html', role=role)
