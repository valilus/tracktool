from flask import jsonify, json

import wtforms
from wtforms import validators
from wtforms.validators import DataRequired


class LoginForm(wtforms.Form):
	email = wtforms.StringField("Email", validators=[validators.DataRequired()])
	password = wtforms.PasswordField("Password", validators=[validators.DataRequired()])
	remember_me = wtforms.BooleanField("Remember me?", default=True)

	def validate(self):
		if not super(LoginForm, self).validate():
			return False

		self.user = User.authenticate(self.email.data, self.password.data)
		if not self.user:
			self.email.errors.append("Invalid email or password.")
			return False

		return True

class OrgForm(wtforms.Form):
    file = wtforms.FileField('Org file')

class RepoForm(wtforms.Form):
    name = wtforms.StringField( 'Name', validators=[DataRequired()])
    description = wtforms.TextAreaField( 'Description' )
    homepage = wtforms.StringField( 'Homepage' )
    private = wtforms.BooleanField( 'Private' )
    has_issues = wtforms.BooleanField( 'Has issues' )
    has_wiki = wtforms.BooleanField( 'Has wiki' )

    # status = wtforms.SelectField( 'Entry status', choices=( (Entry.STATUS_PUBLIC, 'Public'), (Entry.STATUS_DRAFT, 'Draft')), coerce=int)
    # tags = TagField( 'Tags', description='Separate multiple tags with commas.')

    def json(self):
		repoDict = { 
			'name': self.name.data,
			'description': self.description.data,
			'homepage': self.homepage.data,
			'private': self.private.data,
			'has_issues': self.has_issues.data,
			'has_wiki': self.has_wiki.data,
			'auto_init': True
			}

		return repoDict