#!/bin/bash
                               
set -e

export LANGUAGE=en_US.UTF-8
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8
locale-gen en_US.UTF-8
dpkg-reconfigure locales

echo
echo "Environment installation is beginning.  This may take a few minutes ..."

##
#   Install core components    
##

echo
echo "Updating package repositories ..."
sudo apt-get update

##
#   Install python packages
##

echo
echo "Installing ubuntu python packages ..."
sudo apt-get install -y python \
                   python-dev libffi-dev libssl-dev \
                   python-pip \
                   python-software-properties


echo

sudo pip install --upgrade pip -i https://pypi.python.org/simple

echo "Installing python packages ..."
sudo pip install --upgrade setuptools
sudo pip install  -qq -r /vagrant/deploy/requirements.txt

#mkdir -p /vagrant/.pip_download_cache
#export PIP_DOWNLOAD_CACHE=/vagrant/.pip_download_cache
#export VIRTUALENV=/vagrant/env
#pip install -U pip virtualenv
#virtualenv --system-site-packages $VIRTUALENV
#source $VIRTUALENV/bin/activate
#pip install -r /vagrant/deploy/requirements.txt

#if [ $? -gt 0 ]; then
#    echo 2> 'Unable to install python requirements from requirements.txt'
 #   exit 1
#fi

##
#   Setup is complete.
##
echo
echo "The environment has been installed."
echo
echo "You can start the machine by running: vagrant up"
echo "You can ssh to the machine by running: vagrant ssh"
echo "You can stop the machine by running: vagrant halt"
echo "You can delete the machine by running: vagrant destroy"
echo
echo "If this is your first time, you should install the virtual machine guest additions."
echo "To do that, ssh into the machine (vagrant ssh) and run: sudo ./postinstall.sh"
echo


exit 0