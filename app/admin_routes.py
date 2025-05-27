from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../supabase')))
from supabase1.clients import supabase

admin_routes = Blueprint('admin_routes', __name__)

@admin_routes.route('/admin/dashboard')
def admin_dashboard():
    queries = supabase.table('support_queries').select('*').order('submitted_at', desc=True).execute().data
    return render_template('dashboard3.html', queries=queries, enumerate=enumerate)

@admin_routes.route('/admin/query/<int:query_id>')
def view_query(query_id):
    # Get single query from Supabase
    query = supabase.table('support_queries').select('*').eq('id', query_id).execute().data[0]
    return render_template('response_page.html', query=query)

@admin_routes.route('/admin/respond', methods=['POST'])
def respond():
    query_id = request.form.get('query_id')
    response = request.form.get('response')
    query = supabase.table('support_queries').select('query').eq('id', query_id).execute().data[0]['query']
    username = supabase.table('support_queries').select('username').eq('id', query_id).execute().data[0]['username']
    content = f'Query: {query} \n Response: {response}'

    a = {
        'username': username,
        'content': content
    }

    supabase.table('notification').insert(a).execute()
    supabase.table('support_queries').delete().eq('id', query_id).execute()
    
    flash("Response submitted successfully!", "success")
    return redirect(url_for('admin_routes.admin_dashboard'))

@admin_routes.route('/admin/manage-users')
def manage_users():
    users = supabase.table('users').select('*').order('username').execute().data
    return render_template('manage_users.html', users=users)

@admin_routes.route('/admin/freeze-user', methods=['POST'])
def freeze_user():
    username = request.form['username']
    freeze = supabase.table('users').select('frozen').eq('username', username).execute()
    if freeze.data[0]['frozen']: 
        supabase.table('users').update({'frozen': False}).eq('username', username).execute()
        flash(f"User '{username}' unfrozen successfully.", "success")
    else:
        supabase.table('users').update({'frozen': True}).eq('username', username).execute()
        flash(f"User '{username}' frozen successfully.", "success")
    return redirect(url_for('admin_routes.manage_users'))

@admin_routes.route('/admin/delete-user', methods=['POST'])
def delete_user():
    username = request.form['username']
    supabase.table('users').delete().eq('username', username).execute()
    flash(f"User {username} deleted successfully.", "error")
    return redirect(url_for('admin_routes.manage_users'))

@admin_routes.route('/admin/official-requests')
def official_requests():
    pending_officials = supabase.table('users').select('*').eq('role', 'prgi_official').eq('verified', False).execute().data
    return render_template('official_requests.html', pending_officials=pending_officials, enumerate=enumerate)

@admin_routes.route('/admin/approve-official', methods=['POST'])
def approve_official():
    username = request.form['username']
    supabase.table('users').update({'verified': True}).eq('username', username).execute()
    flash(f"{username} approved.", 'success')
    return redirect(url_for('admin_routes.official_requests'))

@admin_routes.route('/admin/reject-official', methods=['POST'])
def reject_official():
    username = request.form['username']
    supabase.table('users').delete().eq('username', username).execute()
    flash(f"{username} rejected and removed.", 'error')
    return redirect(url_for('admin_routes.official_requests'))
