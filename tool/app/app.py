from flask import Flask, request, g, session, redirect, url_for
from flask import render_template_string

from github import GitHub

from flask_script import Manager
from flask_bcrypt import Bcrypt

from config import Configuration

app = Flask(__name__)

app.config.from_object(Configuration)

manager = Manager(app)
bcrypt = Bcrypt(app)
github = GitHub(app)

@app.before_request
def before_request():
	pass

@app.after_request
def after_request(response):
	return response