from flask import Blueprint, render_template, request, url_for, redirect
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../supabase')))
from supabase1.clients import supabase

common_routes = Blueprint('common_routes', __name__)

# Route to display Existing Titles page
@common_routes.route('/existing_titles', methods=['GET', 'POST'])
def existing_titles():
    # Pagination settings
    page = int(request.args.get('page', 1))
    per_page = 10  # Number of titles per page
    offset = (page - 1) * per_page

    # Handle search, sort, and filter
    search_query = request.args.get('search', '')
    sort_by = request.args.get('sort', 'title')  # Default sort is by title
    filter_by = request.args.get('filter', '')

    # Build query
    query = supabase.table('titles')

    # Apply search filter
    if search_query:
        query = query.ilike('title', f'%{search_query}%')

    # Apply language filter
    if filter_by:
        query = query.ilike('language', f'%{filter_by}%')

    # Apply sorting
    if sort_by == 'Title A-Z':
        query = query.order('title', ascending=True)
    elif sort_by == 'Title Z-A':
        query = query.order('title', ascending=False)
    elif sort_by == 'Publisher A-Z':
        query = query.order('publisher', ascending=True)
    elif sort_by == 'Language':
        query = query.order('language', ascending=True)

    # Paginate the query
    titles = query.select('*').limit(per_page).offset(offset).execute()

    # Get total count for pagination
    total_titles = supabase.table('titles').select('id').execute()

    total_pages = len(total_titles.data) // per_page + (1 if len(total_titles.data) % per_page > 0 else 0)

    return render_template(
        'etitles.html',
        titles=titles.data,
        total_pages=total_pages,
        current_page=page,
        search_query=search_query,
        sort_by=sort_by,
        filter_by=filter_by
    )

@common_routes.route('/settings/<username>/')
def settings(username):
    user = supabase.table('users').select('*').eq('username', username).execute().data
    return render_template('Settings.html', current_user=username, user=user[0])

@common_routes.route('/update-settings', methods=['POST'])
def update_settings():
    # Handle form submission
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    if new_password and new_password != confirm_password:
        return "Passwords don't match", 400
        
    # Update user settings...
    return redirect(url_for('settings'))

@common_routes.route('/delete-account', methods=['POST'])
def delete_account():
    # Delete account logic...
    return redirect(url_for('login'))