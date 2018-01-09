# TRACKTASK
Prerequisites


VirtualBox
Download from: https://www.virtualbox.org/wiki/Downloads

Install Vagrant 1.5.x
http://www.vagrantup.com/downloads.html



## Setup
To setup a development environment the following steps must be taken:

### First terminal 

### go inside tool folder
$ cd tool

### boot up vagrant
$ vagrant up

### ssh into vagrant
$ vagrant ssh

### go to source directory
$ cd /vagrant

### go to the app directory
$ cd app

### run the app
python manage.py runserver


### SECOND TERMINAL 

```sh
cd tool/
./ngrok http -region=us -hostname=tracktask.ngrok.io 5000
```

NOW VISIT: http://tracktask.ngrok.io/


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