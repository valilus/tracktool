# TRACKTASK
> Short blurb about what your product does.

One to two paragraph statement about your product and what it does.

## Deployment

### FIRST TERMINAL 

```sh
cd tool/
((source venv/bin/activate))
(( pip install -r requirements.txt ))
cd app/
python manage.py runserver
```

### SECOND TERMINAL 

```sh
cd tool/
(( ./ngrok authtoken 5CRbpMXTsoU8QWjBG3nnA_T1qMPb1vXuWJR3rmKSHM )) 
./ngrok http -region=us -hostname=tracktask.ngrok.io 5000
```

NOW VISIT: http://tracktask.ngrok.io/

### Requirements
* Investigation of project management workflows
* Development of a project management tool
	* Support for task management, monitoring, etc
	* Web-based frontend
	* Git-based backend (text files)
	* support for email based workflows
	* support for multiple users
	* support for different roles (viewer, reporter, developer, etc.)
	* Quick deployment & initialization of new projects
	* Preferred language: Python/Flask  (negotiable)

## Featurest
* support for different roles (viewer, reporter, developer, etc.)
	* viewer 
		* search user by name
		* search repository by name

* Quick deployment & initialization of new projects
	* create repository
	* manage repository 
	* send invitation

## Release History

* 31/12/2017
    * ADD: 'role viewer' possibility to 'search user and repository by name' 
    * FIX: 'update_email_json' problem to change email of collaborators 
    * CHANGE: Layout of 'settings' page
* 30/12/2017
    * ADD: Possibility to 'add more collaborators' in project

## Authors

* **Riccardo Di Curti** - *backend & frontend dev.*
* **Valeric Lupoaie** - *backend & frontend dev.*