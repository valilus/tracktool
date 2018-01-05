from flask import flash, redirect, render_template, request, url_for, Response, Markup 
from werkzeug import secure_filename
from app import app, github 
from functools import wraps
from forms import RepoForm
from flask import jsonify

import markdown
import datetime
import urllib2
import json
import org
import os
import re

def required_auth():
    def wrapper(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if request.cookies.get('github_access_token') is None:
                return redirect(url_for('homepage'))
            return f(*args, **kwargs)
        return wrapped
    return wrapper

##
# HOMEPAGE
##

@app.route('/')
def homepage():
    return render_template('homepage.html')

## 
# SERVICE
##

@app.route('/login/')
def login():
    return github.authorize(scope="user,repo,delete_repo")

@app.route('/logout')
@required_auth()
def logout():
    redirect_to_index = redirect(url_for('homepage'))
    cookie = app.make_response(redirect_to_index)
    cookie.set_cookie('github_access_token', expires=0)
    cookie.set_cookie('username', expires=0)
    flash('You have been logged out.', 'success')
    return cookie

##
# SUBPAGE
##

# @app.route('/test/')
# @required_auth()
# def test():
#     test_dict = github.get("user")
#     return render_template('test.html', test=json.dumps(test_dict, sort_keys = False, indent = 2))

@github.access_token_getter
def token_getter():
    if request.cookies.get('github_access_token') is not None:
        return request.cookies.get('github_access_token')
    else: 
        flash('Authorization failed.')
        return redirect(url_for('homepage'))

##
# SERVICE
##

@app.route('/payload', methods=['POST'])
def webhooks():
    content = request.get_json(silent=True)
    split_dict = content["repository"]["full_name"].split("/")
    # scarico i file in una cartella dedicata 

    print( content )

    github.payload_file_repository(user=split_dict[0], repo=split_dict[1])
    # mando le mail
    github.send_email(content=content)
    return (''), 204

@app.route('/github-callback')
@github.authorized_handler
def authorized(access_token):
    if access_token is None:
        flash('Authorization failed.')
        return redirect(homepage)
    redirect_to_index = redirect(url_for('user'))
    cookie = app.make_response(redirect_to_index)
    cookie.set_cookie('github_access_token', access_token)
    flash('You have been logged in.', 'success')
    return cookie

##
# VIEWER
# user not logged that can search project and user
##

@app.route('/search')
@required_auth()
def search():
    return render_template('search.html')

@app.route('/search_repository_user', methods=['POST'])
@required_auth()
def search_repository_user():
    if request.method == 'POST':
        #TODO: check text not NULL
        result_json = github.search_switcher(tipology=request.form['tipology'], text=request.form['text'])
        return render_template('test.html', test=json.dumps(result_json, sort_keys = False, indent = 2))


##
# USER
##

@app.route('/user')
@required_auth()
def user():
    user = github.get('user')

    print(user["email"])
    print(user["name"])

    if user["email"] == None or user["name"] == None:
        return redirect(url_for('user_missing_data'))

    redirect_to_index = render_template('user.html', user=user)
    cookie = app.make_response(redirect_to_index)
    cookie.set_cookie('username', user['login'])
    return cookie

@app.route('/user_missing_data')
@required_auth()
def user_missing_data():
    user = github.get('user')
    return render_template('user_missing_data.html', user=user)

##
# EVENTS
##

@app.route('/events')
@required_auth()
def events():
    link = 'users/' + request.cookies.get('username') + '/events'
    github.get(link)
    event_dict = github.get(link)
    return render_template('events.html', events=event_dict)

##
# PROJECTS
##


@app.route('/dashboard')
@required_auth()
def dashboard():
    repo_dict = github.get('user/repos')
    return render_template('dashboard.html', repos=repo_dict)


@app.route('/repos')
@required_auth()
def repos():
    repo_dict = github.get('user/repos')
    return render_template('repositories.html', repos=repo_dict)

###
# REPOS  
###

@app.route('/repo/<user>/<repo>/<n>')
@required_auth()
def repo(user, repo, n):

    admin = False

    if user == request.cookies.get('username'):
        admin = True

    github.check_repository(admin=admin, user=user, repo=repo)
    
    if n is 0:
        # print("n: " + str(n))
        repository_folder = "static/repository/" + user + "-" + repo    
    else: 
        # print("n: " + str(n))
        repository_folder = github.download_file_repository(user=user, repo=repo)

    readme_path = repository_folder + "/README.md" 
    project_path = repository_folder + "/project.org"

    repo_dict = github.get('repos/' + user + '/' + repo)
    contents_dict = github.get('repos/' + user + '/' + repo + '/contents')
    collaborators_dict = github.get('repos/' + user + '/' + repo + '/collaborators')
    events_dict = github.get('repos/' + user + '/' + repo + '/events')

    with open(readme_path, "r") as f:
        readme_content = f.readlines()

    readme_content = ''.join(readme_content)

    projects_dict = org.display(project_path)

    if admin:
        hook = github.exist_hook(user=user, repo=repo)
        return render_template('repository.html', admin=admin, repos=repo_dict, contents=contents_dict, collaborators=collaborators_dict, events=events_dict, readme=Markup(markdown.markdown(readme_content)), projects=projects_dict, hook=hook)
   
    else:
        hook = False
        return render_template('repository.html', admin=admin, repos=repo_dict, contents=contents_dict, collaborators=collaborators_dict, events=events_dict, readme=Markup(markdown.markdown(readme_content)), projects=projects_dict, hook=hook)

##
# SERVICE - COLLABORATOR
##

@app.route('/repo_add_collaborator', methods=['POST'])
def repo_add_collaborator():
    split_dict = request.form['submit'].split("/")
    repository_folder = "static/repository/" + split_dict[0] + "-" + split_dict[1]

    if request.form['username']:
        collaborator = request.form['username']
        return redirect(url_for('add_user_to_project', user=split_dict[0], repo=split_dict[1], collaborator=collaborator))
    else: 
        flash('Data is missing in the form.', 'warning')

@app.route('/add_user_to_project/<user>/<repo>/<collaborator>', methods=['GET', 'POST'])
@required_auth()
def add_user_to_project(user, repo, collaborator):

    if request.method == 'POST':
        invitation_json = github.add_user_as_a_collaborator(user=user, repo=repo, collaborator=collaborator)
        print(invitation_json)
        flash('Invitation is sent.', 'success')
        return redirect(url_for('repo', user=user, repo=repo, n=1))

    collaborator_json =github.get_user(collaborator)    
    return render_template('add_user_to_project.html', user=user, repo=repo, collaborator=collaborator_json)

##
# SERVICE - PROJECT
##

@app.route('/iteratefiles')
def navigate(): 
    repo = request.args.get('repo')
    url = request.args.get('url')
    contents_dict = github.get('repos/' + request.cookies.get('username') + '/' + repo + '/contents' + '/' + url)
    print('path: ' + 'repos/' + request.cookies.get('username') + '/' + repo + '/contents' + '/' + url)
    return jsonify(contents_dict)

@app.route('/new_webhooks', methods=['POST'])
def new_webhooks():
    split_dict = request.form['submit'].split("/")
    github.create_hook(user=split_dict[0], repo=split_dict[1])
    return redirect(url_for('repo', user=split_dict[0], repo=split_dict[1], n=0))

@app.route('/org_add_todo', methods=['POST'])
def org_add_todo():

    split_dict = request.form['submit'].split("/")

    repository_folder = "static/repository/" + split_dict[0] + "-" + split_dict[1]
    project_path = repository_folder + "/project.org"

    if request.form['title'] and request.form['content'] and request.form['tags'] and request.form['datetimepicker1']:
        org.create_todo(path=project_path, heading=request.form['title'], priority=request.form['livello'], collaborator=request.form['collaborator'], tags=request.form['tags'], content=request.form['content'], deadline=request.form['datetimepicker1'])
        github.update_orgfile(repository=request.form['submit'], path=project_path)

        flash('Exactly inserted.', 'success')
    else: 
        flash('Data is missing in the form.', 'warning')

    return redirect(url_for('repo', user=split_dict[0], repo=split_dict[1], n=0))

@app.route('/org_add_title', methods=['POST'])
def org_add_title():

    split_dict = request.form['submit'].split("/")

    repository_folder = "static/repository/" + split_dict[0] + "-" + split_dict[1]
    project_path = repository_folder + "/project.org"

    if request.form['title'] and request.form['content']:

        org.create_title(path=project_path, heading=request.form['title'], content=request.form['content'])
        github.update_orgfile(repository=request.form['submit'], path=project_path)

        flash('Exactly inserted.', 'success')
    else: 
        flash('Data is missing in the form.', 'warning')
    
    return redirect(url_for('repo', user=split_dict[0], repo=split_dict[1], n=0))


##
# NUOVI METODI 
##

@app.route('/org_edit_title', methods=['POST'])
def org_edit_title():

    split_dict = request.form['repo'].split("/")

    repository_folder = "static/repository/" + split_dict[0] + "-" + split_dict[1]
    project_path = repository_folder + "/project.org"
    
    return redirect(url_for('repo', user=split_dict[0], repo=split_dict[1], n=0))

@app.route('/org_remove_title', methods=['POST'])
def org_remove_title():

    split_dict = request.form['repo'].split("/")

    repository_folder = "static/repository/" + split_dict[0] + "-" + split_dict[1]
    project_path = repository_folder + "/project.org"

    org.remove_title(path=project_path, index=request.form["enumerate"])
    github.update_orgfile(repository=request.form['repo'], path=project_path)
    
    return redirect(url_for('repo', user=split_dict[0], repo=split_dict[1], n=0))

@app.route('/org_set_done_todo', methods=['POST'])
def org_set_done_todo():

    split_dict = request.form['repo'].split("/")

    repository_folder = "static/repository/" + split_dict[0] + "-" + split_dict[1]
    project_path = repository_folder + "/project.org"

    org.set_done(path=project_path, index=request.form["enumerate"])
    github.update_orgfile(repository=request.form['repo'], path=project_path)
    
    return redirect(url_for('repo', user=split_dict[0], repo=split_dict[1], n=0))

@app.route('/org_edit_todo', methods=['POST'])
def org_edit_todo():

    split_dict = request.form['repo'].split("/")

    repository_folder = "static/repository/" + split_dict[0] + "-" + split_dict[1]
    project_path = repository_folder + "/project.org"
    
    return redirect(url_for('repo', user=split_dict[0], repo=split_dict[1], n=0))

@app.route('/org_remove_todo', methods=['POST'])
def org_remove_todo():

    split_dict = request.form['repo'].split("/")

    repository_folder = "static/repository/" + split_dict[0] + "-" + split_dict[1]
    project_path = repository_folder + "/project.org"

    org.remove_todo(path=project_path, index=request.form["enumerate"])
    github.update_orgfile(repository=request.form['repo'], path=project_path)
    
    return redirect(url_for('repo', user=split_dict[0], repo=split_dict[1], n=0))

##
# EDIT - PROJECT
##

@app.route('/repos/create', methods=['GET', 'POST'])
@required_auth()
def crepo():
    if request.method == 'POST':
        form = RepoForm(request.form)
        if form.validate():
            data = form.json()
            github.post('user/repos', data=data)
            flash('Repo created successfully.', 'success')
            return redirect(url_for('repos'))
    else:
        form = RepoForm()
    return render_template('create.html', form=form)

@app.route('/repo/<slug>/delete', methods=['GET', 'POST'])
@required_auth()
def drepo(slug):
    if request.method == 'POST':
        github.delete('repos/' + request.cookies.get('username') + '/' + slug)
        flash('Repo has been deleted.', 'success')
        return redirect(url_for('repos'))
    return render_template('delete.html', slug=slug)

@app.route('/repo/<slug>/edit', methods=['GET', 'POST'])
@required_auth()
def erepo(slug):
    if request.method == 'POST':
        form = RepoForm(request.form)
        if form.validate():
            github.patch('repos/' + request.cookies.get('username') + '/' + slug, data=form.json())
            flash('Repo has been edit.', 'success')
            return redirect(url_for('repos'))
    else:
        form = RepoForm()
    return render_template('edit.html', slug=slug, form=form)

##
# SETTINGS
##

@app.route('/settings')
@required_auth()
def settings():
    # get static/repository/list.txt in json format
    hook_dict = github.list_json(user=request.cookies.get('username'))
    print(hook_dict) # print in terminal 
    return render_template('settings.html', hooks=hook_dict)

@app.route('/settings_update_email', methods=['POST'])
def settings_update_email():
    if not request.form['email']:
        flash('Insert a valid E-Mail.', 'warning')
        return redirect(url_for('settings'))
    else:
        split_dict = request.form['submit'].split("/")
        user = request.form['utente']
        new_email = request.form['email']
        github.update_email_json(repo=split_dict[1], user=split_dict[0], collaborator=user, email=new_email)
        flash('Email updated.', 'success')
        return redirect(url_for('settings'))

##
# ERROR
##

@app.errorhandler(403)
def page_forbidden(error):
    return render_template('403.html'), 403

@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(410)
def page_forbidden(error):
    return render_template('410.html'), 410

@app.errorhandler(500)
def internal_server_error(error):
    return render_template('500.html'), 500