from flask import Blueprint, render_template, request, redirect, url_for, flash
from datetime import datetime
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../supabase')))
from supabase1.clients import supabase  # Assuming supabase client is already initialized
from jellyfish import jaro_winkler_similarity, metaphone
import spacy
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer

user_routes = Blueprint('user_routes', __name__)

model = SentenceTransformer('paraphrase-MiniLM-L6-v2', device='cpu')

def preprocess_title(title):
    # Remove stopwords and trivial words
    stopwords = {"the", "a", "an", "of", "in", "and"}
    return " ".join([word for word in title.lower().split() 
                    if word not in stopwords])

def calculate_similarity(sent1, sent2):
    # 1. Spelling (word-level average)
    # 1. Preprocess (remove stopwords)
    clean1, clean2 = preprocess_title(sent1), preprocess_title(sent2)
    
    # 2. Spelling (Jaccard similarity on words)
    words1, words2 = set(clean1.split()), set(clean2.split())
    spelling = len(words1 & words2) / len(words1 | words2)
    
    # 3. Phonetics (Metaphone of entire string)
    phon1 = "".join([metaphone(word) for word in clean1.split()])
    phon2 = "".join([metaphone(word) for word in clean2.split()])
    phonetic = jaro_winkler_similarity(phon1, phon2)
    
    # 4. Semantics (TF-IDF + Cosine)
    vectorizer = TfidfVectorizer().fit_transform([clean1, clean2])
    semantic = (vectorizer[0] @ vectorizer[1].T).toarray()[0][0]
    
    # 5. Combined score (prioritize word overlap)
    
    # Combine scores (adjust weights as needed)
    if spelling == 1.0 or phonetic == 1.0 or semantic == 1.0:
        return 100.0
    
    # Case 2: Weighted average with bonus for partial matches
    weighted_avg = (spelling*0.4 + phonetic*0.3 + semantic*0.3)
    
    # Bonus: If any two dimensions are > 80% match, boost score
    high_matches = sum([x > 0.8 for x in [spelling, phonetic, semantic]])
    if high_matches >= 2:
        weighted_avg = min(weighted_avg * 1.2, 1.0)  # Cap at 100%
    
    return round(weighted_avg * 100, 2)

# Function to check if the title violates any rules (restricted words, prefix/suffix, etc.)
def check_title_rules(title: str) -> bool:
    # Check restricted words
    restricted_words = supabase.table('restricted_words').select('word').execute().data
    title_words = title.lower().split()
    for word in restricted_words:
        if word in title_words:
            return False  # Title contains a restricted word
    
    # Check disallowed prefixes and suffixes
    disallowed_prefixes_suffixes = supabase.table('restricted_affixes').select('affix','type').execute().data
    for item in disallowed_prefixes_suffixes:
        if item['type'] == 'prefix':
            if title.lower().startswith(item['affix']):
                return False
        else:
            if title.lower().endswith(item['affix']):
                return False
          # Title contains disallowed prefix/suffix
    
    # No rules violated
    return True

# Function to calculate verification probability
def calculate_verification_probability(similarity_score: float, title_violates_rules: bool) -> float:
    if title_violates_rules:
        return 0.0  # Probability is 0 if any rule is violated
    return 100.0 - similarity_score  # Verification probability = 100 - similarity score

# Route for Title Applicant Dashboard
@user_routes.route('/title_applicant_dashboard/<username>/')
def title_applicant_dashboard(username):
    return render_template('dashboard1.html', user=username)
 
# Route for analyzing title
@user_routes.route('/analysis/<username>/', methods=['GET', 'POST'])
def analyze_title(username):
    # Retrieve the title submitted by the applicant
    title=request.form['title']
    
    # Retrieve all existing titles
    existing_titles = supabase.table('titles').select('title').execute().data
    accepted_titles = supabase.table('verification_history').select('title','username').eq('result', 'accepted').execute().data
    
    for i in accepted_titles:
        if i['username']!=username:
            existing_title.append({'title':i['title']})

    similarity_scores = []
    
    # Calculate similarity for all existing titles
    for existing_title in existing_titles:
        score = calculate_similarity(title, existing_title['title'])
        similarity_scores.append({
            'title': existing_title['title'],
            'similarity': score
        })
    
    # Find the highest similarity
    max_similarity = max(similarity_scores, key=lambda x: x['similarity'])
    
    # Check if any title rules are violated
    title_violates_rules = not check_title_rules(title)
    
    # Calculate the verification probability
    verification_prob = calculate_verification_probability(max_similarity['similarity'], title_violates_rules)
    
    prob = 50

    # Determine final status and feedback if rejected
    status = "Accepted" if verification_prob >= prob else "Rejected"
    feedback = ""
    
    if status == "Rejected":
        if title_violates_rules:
            feedback="Your title contains restricted words or restricted affixes"
        else:
            feedback="Your title is too similar to the title -- "+ max_similarity['title']
    
    # Store verification result in history (Supabase)
    supabase.table('verification_history').insert({  # Assuming user_id is available in the title data
        'title': title,
        'result': status,
        'username': username
    }).execute()

    return render_template(
        'analysis.html',
        title=title,
        similarity_scores=sorted(similarity_scores, key= lambda x:x['similarity'], reverse=True),
        similarity_percentage=max_similarity['similarity'],
        verification_probability=verification_prob,
        status=status,
        feedback=feedback,
        enumerate=enumerate,
        username=username,
        round=round
    )

# Route for registering the title (if accepted)
@user_routes.route('/register_title/<username>/<title>/', methods=['GET', 'POST'])
def register_title(username, title):
    if request.method == 'POST':
        title_data = request.form.to_dict()  # Get form data
        # Insert into the main titles table (Supabase)
        supabase.table('registration_history').insert({
            'title': title,
            'language': title_data['language'],
            'periodicity': title_data['periodicity'],
            'place': title_data['place'],
            'category': title_data['category'],
            'format': title_data['format'],
            'justification': title_data['justification'],
            'owner': title_data['owner-name'],
            'publisher': title_data['publisher-name'],
            'legal_entity': title_data['legal-entity'],
            'applicant_name': title_data['applicant-name'],
            'applicant_username': title_data['applicant-username'],
            'applicant_email': title_data['applicant-email']
        }).execute()

        flash('Registration Request sent successfully...', 'success')
        return redirect(url_for('user_routes.title_applicant_dashboard', username=username))
    user = supabase.table('users').select('username', 'full_name', 'email').eq('username',username).execute().data[0]
    return render_template('registration.html', username=username, title=title, user=user)

# Route to view user history (Verification and Registration)
@user_routes.route('/history/<username>/')
def user_history(username):
    # Fetch verification history (from Supabase)
    
    verification_history = supabase.table('verification_history').select('*').eq('username', username).execute().data
    
    # Fetch registration history (from Supabase)
    registration_history = supabase.table('registration_history').select('*').eq('applicant_username', username).execute().data
    
    return render_template('history.html', 
                           verification_history=verification_history, 
                           registration_history=registration_history,
                           enumerate=enumerate, username=username)

@user_routes.route('/title/<int:id>')
def title_description(id):
    record = supabase.table('registration_history').select('*').eq('id', id).execute().data
    return render_template('title_desc.html', desc=record)

@user_routes.route('/title_cancel/<int:id>/<username>')
def title_cancel(id, username):
    supabase.table('registration_history').delete().eq('id', id).execute()
    flash('Cancelled...', 'success')
    return redirect(url_for('user_routes.user_history', username=username))
