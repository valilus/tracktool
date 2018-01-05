###
#   an upgraded version of GitHub-Flask
#   from https://github.com/cenkalti/github-flask
####

import logging
try:
    from urllib.parse import urlencode, parse_qs
except ImportError:
    from urllib import urlencode
    from urlparse import parse_qs
from functools import wraps

import io
import os
import urllib2
import zipfile
import requests

from flask import redirect, request, json
from flask_mail import Mail, Message

from datetime import datetime
from dateutil.tz import tzoffset
from threading import Thread

__version__ = '3.1.6'

_logger = logging.getLogger(__name__)
# Add NullHandler to prevent logging warnings on startup
null_handler = logging.NullHandler()
_logger.addHandler(null_handler)


def is_valid_response(response):
    return 200 <= response.status_code <= 299


def is_json_response(response):
    content_type = response.headers.get('Content-Type', '')
    return content_type == 'application/json' or content_type.startswith('application/json;')

#Class that is used to handle failures of requests to the GitHub API
class GitHubError(Exception):

#returns the message associated with the error provided by the API as readable strings.
    def __str__(self):
        try:
            message = self.response.json()['message']
        except Exception:
            message = None
        return "%s: %s" % (self.response.status_code, message)

    @property
    def response(self):
        return self.args[0]

class GitHub(object):
    """
    Provides decorators for authenticating users with GitHub within a Flask
    application. Helper methods are also provided interacting with GitHub API.

    """
    BASE_URL = 'https://api.github.com/'
    BASE_AUTH_URL = 'https://github.com/login/oauth/'

    mail = None

    def __init__(self, app=None):
        if app is not None:
            self.app = app
            self.init_app(self.app)
            self.init_mail(self.app)
        else:
            self.app = None

    def init_app(self, app):
        self.client_id = app.config['GITHUB_CLIENT_ID']
        self.client_secret = app.config['GITHUB_CLIENT_SECRET']
        self.base_url = app.config.get('GITHUB_BASE_URL', self.BASE_URL)
        self.auth_url = app.config.get('GITHUB_AUTH_URL', self.BASE_AUTH_URL)
        self.session = requests.session()

    def init_mail(self, app):
        self.mail = Mail(app)

    def access_token_getter(self, f):
        """
        Registers a function as the access_token getter. Must return the
        access_token used to make requests to GitHub on the user's behalf.

        """
        self.get_access_token = f
        return f

    def get_access_token(self):
        raise NotImplementedError

    def authorize(self, scope=None, redirect_uri=None, state=None):
        """
        Redirect to GitHub and request access to a user's data.

        :param scope: List of `Scopes`_ for which to request access, formatted
                      as a string or comma delimited list of scopes as a
                      string. Defaults to ``None``, resulting in granting
                      read-only access to public information (includes public
                      user profile info, public repository info, and gists).
                      For more information on this, see the examples in
                      presented in the GitHub API `Scopes`_ documentation, or
                      see the examples provided below.
        :type scope: str
        :param redirect_uri: `Redirect URL`_ to which to redirect the user
                             after authentication. Defaults to ``None``,
                             resulting in using the default redirect URL for
                             the OAuth application as defined in GitHub.  This
                             URL can differ from the callback URL defined in
                             your GitHub application, however it must be a
                             subdirectory of the specified callback URL,
                             otherwise raises a :class:`GitHubError`.  For more
                             information on this, see the examples in presented
                             in the GitHub API `Redirect URL`_ documentation,
                             or see the example provided below.
        :type redirect_uri: str
        :param state: An unguessable random string. It is used to protect
                      against cross-site request forgery attacks.
        :type state: str

        For example, if we wanted to use this method to get read/write access
        to user profile information, in addition to read-write access to code,
        commit status, etc., we would need to use the `Scopes`_ ``user`` and
        ``repo`` when calling this method.

        .. code-block:: python

            github.authorize(scope="user,repo")

        Additionally, if we wanted to specify a different redirect URL
        following authorization.

        .. code-block:: python

            # Our application's callback URL is "http://example.com/callback"
            redirect_uri="http://example.com/callback/my/path"

            github.authorize(scope="user,repo", redirect_uri=redirect_uri)


        .. _Scopes: https://developer.github.com/v3/oauth/#scopes
        .. _Redirect URL: https://developer.github.com/v3/oauth/#redirect-urls

        """
        _logger.debug("Called authorize()")
        params = {'client_id': self.client_id}
        if scope:
            params['scope'] = scope
        if redirect_uri:
            params['redirect_uri'] = redirect_uri
        if state:
            params['state'] = state

        url = self.auth_url + 'authorize?' + urlencode(params)
        _logger.debug("Redirecting to %s", url)
        return redirect(url)

    def authorized_handler(self, f):
        """
        Decorator for the route that is used as the callback for authorizing
        with GitHub. This callback URL can be set in the settings for the app
        or passed in during authorization.

        """
        @wraps(f)
        def decorated(*args, **kwargs):
            if 'code' in request.args:
                data = self._handle_response()
            else:
                data = self._handle_invalid_response()
            return f(*((data,) + args), **kwargs)
        return decorated

    def _handle_response(self):
        """
        Handles response after the redirect to GitHub. This response
        determines if the user has allowed the this application access. If we
        were then we send a POST request for the access_key used to
        authenticate requests to GitHub.

        """
        _logger.debug("Handling response from GitHub")
        params = {
            'code': request.args.get('code'),
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        url = self.auth_url + 'access_token'
        _logger.debug("POSTing to %s", url)
        _logger.debug(params)
        response = self.session.post(url, data=params)
        data = parse_qs(response.content)
        _logger.debug("response.content = %s", data)
        for k, v in data.items():
            if len(v) == 1:
                data[k] = v[0]
        token = data.get(b'access_token', None)
        if token is not None:
            token = token.decode('ascii')
        return token

    def _handle_invalid_response(self):
        pass

    def raw_request(self, method, resource, access_token=None, **kwargs):
        """
        Makes a HTTP request and returns the raw
        :class:`~requests.Response` object.

        """

        print("KWARGS: ")
        print(kwargs)

        # Set ``Authorization`` header
        kwargs.setdefault('headers', {})
        if access_token is None:
            print("ACCESS_ TOKEN: ")
            access_token = self.get_access_token()
            print(access_token)
        kwargs['headers'] = kwargs['headers'].copy()
        kwargs['headers'].setdefault('Authorization', 'token %s' % access_token)

        if resource.startswith(("http://", "https://")):
            url = resource
        else:
            url = self.base_url + resource
        return self.session.request(method, url, allow_redirects=True, **kwargs)

    def request(self, method, resource, all_pages=False, **kwargs):
        """
        Makes a request to the given endpoint.
        Keyword arguments are passed to the :meth:`~requests.request` method.
        If the content type of the response is JSON, it will be decoded
        automatically and a dictionary will be returned.
        Otherwise the :class:`~requests.Response` object is returned.

        """

        response = self.raw_request(method, resource, **kwargs)

        if not is_valid_response(response):
            raise GitHubError(response)

        if is_json_response(response):
            result = response.json()
            while all_pages and response.links.get('next'):
                url = response.links['next']['url']
                response = self.raw_request(method, url, **kwargs)
                if not is_valid_response(response) or \
                        not is_json_response(response):
                    raise GitHubError(response)
                    pass
                body = response.json()
                if isinstance(body, list):
                    result += body
                elif isinstance(body, dict) and 'items' in body:
                    result['items'] += body['items']
                else:
                    raise GitHubError(response)
            return result
        else:
            return response

    def get(self, resource, params=None, **kwargs):
        """Shortcut for ``request('GET', resource)``."""
        return self.request('GET', resource, params=params, **kwargs)

    def post(self, resource, data=None, **kwargs):
        """Shortcut for ``request('POST', resource)``.
        Use this to make POST request since it will also encode ``data`` to
        'application/json' format."""
        headers = dict(kwargs.pop('headers', {}))
        headers.setdefault('Content-Type', 'application/json')
        data = json.dumps(data)
        return self.request('POST', resource, headers=headers,
                            data=data, **kwargs)

    def head(self, resource, **kwargs):
        return self.request('HEAD', resource, **kwargs)

    def patch(self, resource, data=None, **kwargs):
        headers = dict(kwargs.pop('headers', {}))
        headers.setdefault('Content-Type', 'application/json')
        data = json.dumps(data)
        return self.request('PATCH', resource, headers=headers,
                            data=data, **kwargs)

    def put(self, resource, data=None, **kwargs):
        headers = dict(kwargs.pop('headers', {}))
        headers.setdefault('Content-Type', 'application/json')
        data = json.dumps(data)
        return self.request('PUT', resource, headers=headers,
                            data=data, **kwargs)

    def delete(self, resource, **kwargs):
        return self.request('DELETE', resource, **kwargs)

    #############################
    ##### MY IMPLEMENTATION #####
    #############################

    #########
    # EMAIL
    #########

    #def send_email(self, content):
    #   with open('static/repository/list.txt') as data_file:    
    #      data = json.load(data_file)
    #
    #      user_dict = content["repository"]["full_name"]
    #
    #    print(user_dict)

    def send_async_email(self, msg):
        with self.app_context():
            mail.send(msg)

    def send_email(to, subject, email):
        msg = Message(self.config['FLASKY_MAIL_SUBJECT_PREFIX'] + subject,
                  sender=self.config['FLASKY_MAIL_SENDER'], recipients=[])
        msg.recipients = [email]
        #msg.html = render_template(template + '.html', **kwargs) 
        thr = Thread(target=send_async_email, args=[self, msg]) 
        thr.start()
        return thr        

    def send_login(self, email, username): 
        msg = Message("[TRACKtask] - login", recipients=[])
        msg.recipients = [email]
        msg.html = "Hello, <b>" + username + "</b> </br> you have just accessed tracktask.com"
        self.mail.send(msg)

    def send_payload(self, email, username, repository): 
        msg = Message("[TRACKtask] - notification", recipients=[])
        msg.recipients = [email]
        msg.html = "Hello, <b>" + username + "</b> </br> you have just received an actualization regarding your folder: " + repository
        self.mail.send(msg)    

    def send_newhook(self, email, username, repository):
        msg = Message("[TRACKtask] - notification", recipients=[])
        msg.recipients = [email]
        msg.html = "Hello, <b>" + username + "</b> </br> you have created a new web hook through tracktask.com (" + repository + ")"
        self.mail.send(msg)

    #########
    # HELPERS
    #########

    def subfolders(self, path):

        dirs = os.listdir(path)
        subdirectory = str(False)

        for sub in dirs:
            subdirectory = sub

        if subdirectory == str(False): 
            return False

        return path + "/" + subdirectory

    def remove_folder(self, path):
        for root, dirs, files in os.walk(path, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))

    def file_to_binary(self, path): 
        with io.open(path,'r',encoding='utf8') as f:
            text = f.read()
        f.close()
        return text

    def get_now(self):
        now = datetime.now()
        return now.strftime("%Y-%m-%dT%H:%M:%SZ")

    def check_repository(self, admin, user, repo):
        repository = user + "/" + repo
        contents_dict = self.get('repos/' + repository + '/contents')

        control_readme = True
        control_project = True

        if contents_dict[0].has_key("message"):
            pass

        for s in contents_dict:
            if "README.md" in s["name"]:
                control_readme = False 
                pass

        for s in contents_dict:
            if "project.org" in s["name"]:
                control_project = False 
                pass

        if control_readme: 
            self.create_readme(repository=repository)

        if control_project: 
            self.create_orgfile(repository=repository)

    # scarico unicamente il readme ed il file org
    def download_file_repository(self, user, repo):
        dir_name = "static/repository/" + user + "-" + repo

        readme_dict = self.get("repos/" + user + "/" + repo + "/contents/README.md")
        project_dict = self.get("repos/" + user + "/" + repo + "/contents/project.org")

        if os.path.isdir(dir_name):
            self.remove_folder(dir_name)

        if not os.path.exists(dir_name):
            os.makedirs(dir_name)

        readme_path = dir_name + "/README.md"
        project_path = dir_name + "/project.org"

        response = urllib2.urlopen(readme_dict["download_url"])
        readme_content = response.read()

        response = urllib2.urlopen(project_dict["download_url"])
        project_content = response.read()

        with open(readme_path,'wb') as f:
            f.write(readme_content)

        with open(project_path,'wb') as f:
            f.write(project_content)

        return dir_name 

    # scarico unicamente il readme ed il file org
    def payload_file_repository(self, user, repo):
        dir_name = "static/payload/" + user + "-" + repo

        if os.path.isdir(dir_name):
            self.remove_folder(dir_name)

        if not os.path.exists(dir_name):
            os.makedirs(dir_name)

        project_path = dir_name + "/project.org"

        download_url = 'https://raw.githubusercontent.com/' + user + '/' + repo + '/master/project.org' 

        response = urllib2.urlopen(download_url)
        project_content = response.read()

        with open(project_path,'wb') as f:
            f.write(project_content)

        return dir_name 

    def download_repo(self, user, repo):
        repo_dir = "static/repository/" + user + "-" + repo

        if (os.path.isdir(repo_dir)):
            repository_folder = self.subfolders(repo_dir)
            if repository_folder != False:
                pass
        else: 
            self.remove_folder(repo_dir)

        url = "repos/" + user +  "/" + repo + "/zipball"
        dir_name = "static/repository/" + user + "-" + repo

        if os.path.isdir(dir_name):
            self.remove_folder(dir_name)

        file_name = dir_name + ".zip"
        r = self.get("repos/" + user +  "/" + repo + "/zipball", stream=True)

        if type(r) is dict: 
            pass
        else:
            with open(file_name, 'wb') as fd:
                for chunk in r.iter_content(chunk_size=128):
                    fd.write(chunk)

            fd.close()
            self.unzip(file_name=file_name, dir_name=dir_name)

        repository_folder = self.subfolders(repo_dir)
        return repository_folder

    def unzip(self, file_name, dir_name):
        with zipfile.ZipFile(file_name, "r") as zf:
            zf.extractall(dir_name)  
        zf.close()
        os.remove(file_name) 

    def update_json(self, user, repo):
        collaborators_dict = self.list_collaborators(user=user, repo=repo)
        json_file = open('static/repository/list.txt', 'r')
        json_dict = json.load(json_file)
        json_file.close()
        email_list = dict()
        for collaborator in collaborators_dict:
            collaborator_dict = self.get_user(collaborator["login"])
            if collaborator_dict["email"]:
                self.send_newhook(collaborator_dict["email"], collaborator["login"], request.form['submit'])
            email_list[collaborator["login"]] = collaborator_dict["email"]
        repository = user + "/" + repo
        json_dict[repository] = email_list    
        with open('static/repository/list.txt', 'w') as f:
            json.dump(json_dict, f, ensure_ascii=False)

    def list_json(self, user): 
        json_file = open('static/repository/list.txt', 'r')
        json_dict = json.load(json_file)
        json_file.close()
        json_new = dict()
        for repo in json_dict:
            split_dict = repo.split("/")
            if split_dict[0] == user:
                json_new[repo] = json_dict[repo]
        return json_new

    def update_email_json(self, repo, user, collaborator, email): 
        json_file = open('static/repository/list.txt', 'r')
        json_dict = json.load(json_file)
        json_file.close()

        repository = user + "/" + repo
        json_dict[repository][collaborator] = email    
        with open('static/repository/list.txt', 'w') as f:
            json.dump(json_dict, f, ensure_ascii=False)

    #########
    # SEARCH
    #########

    def search_switcher(self, tipology, text): 

        print(tipology)

        if tipology  == 'REPOSITORY': 
            return self.search_repository(repositoryname=text)
        else: 
            return self.search_user(username=text)


    # Search users
    # Find users via various criteria. (This method returns up to 100 results per page.)
    # GET /search/users
    def search_user(self, username): 
        
        params = {
            "q": username 
        }

        print(params)

        json = self.get("search/users", params=params)
        return json

    # Search repositories
    # Find repositories via various criteria. This method returns up to 100 results per page.
    # GET /search/repositories
    def search_repository(self, repositoryname): 
        
        params = {
            "q": repositoryname 
        }

        print(params)

        json = self.get("search/repositories", params=params)
        return json

    #TODO: implement search issuere , incode, etc...     

    #########
    # USER
    #########

    def get_username(self):
        json = self.get('user')
        return json["login"]

    def get_name(self):
        json = self.get('user')
        return json["name"]

    def get_email(self):
        json = self.get('user')
        return json["email"]

    def get_user(self, username): 
        json = self.get("users/" + username)
        return json

    #########
    # REPOSITORY
    #########

    def list_repositories(self): 
        pass

    def get_repository(self, user, repo):
        json = self.get("repos/" + user + "/" + repo)
        return json

    def list_collaborators(self, user, repo):
        json = self.get("repos/" + user + "/" + repo)
        return json

    #########
    # COLLABORATORS
    #########

    def list_collaborators(self, user, repo): 
        json = self.get("repos/" + user + "/" + repo + "/collaborators")
        return json

    #Add user as a collaborator
    # PUT /repos/:owner/:repo/collaborators/:username
    # permission: push - can pull and push, but not administer this repository.

    #TODO: MANAGE PERMISSION

    def add_user_as_a_collaborator(self, user, repo, collaborator):
        json = self.put("repos/" + user + "/" + repo + "/collaborators/" + collaborator)
        return json


    #########
    # COMMIT & PUSH
    #########

    def create_blob(self, user, repo, content): 
        data = { 
            "content": content, 
            "encoding": "utf-8" 
        }
        return self.post('repos/' + user + '/' + repo + '/git/blobs', data)

    def get_tree(self): 
        pass

    def create_tree(self, user, repo, base_tree, path, gtype, content): 

        if ("blob" in gtype): 
            mode = "100644"
            sha = content["sha"]

        if ("tree" in gtype): 
            mode = "040000"
            sha = content["sha"]

        if ("commit" in gtype): 
            mode = "160000"
            sha = content["sha"]

        trees = [{
            "path": path,
            "mode": mode,
            "type": gtype,
            "sha": sha
            }]

        data = {
            "base_tree": base_tree, 
            "tree": trees
            }

        return self.post('repos/' + user + '/' + repo + '/git/trees', data)

    def get_commit(self, user, repo, sha): 
        return self.get('repos/' + user + '/' + repo + '/git/commits/' + sha)

    def create_commit(self, user, repo, message, tree, parents): 
        data = { 
            "message": message, 
            "author": {
                "name": self.get_name(),
                "email":self.get_email(),
                "date": self.get_now()
                },
            "parents": parents,
            "tree": tree
            }
        return self.post('repos/' + user + '/' + repo + '/git/commits', data)

    def get_all_reference(self, user, repo): 
        return self.get('repos/' + user + '/' + repo + '/git/refs/')

    def get_reference(self, user, repo, ref):
        return self.get('repos/' + user + '/' + repo + '/git/' + ref) 

    def update_reference(self, user, repo, sha, ref): 
        data = {
            "sha": sha,
            "force": True
        }
        return self.patch('repos/' + user + '/' + repo + '/git/' + ref, data)

    def create_readme(self, repository): 
        split_dict = repository.split("/")
        blob_dict = self.create_blob(user=split_dict[0], repo=split_dict[1], content=self.file_to_binary("static/repository/seample/readme.md"))
        reference_all_dict = self.get_all_reference(user=split_dict[0], repo=split_dict[1])
        reference_dict = self.get_reference(user=split_dict[0], repo=split_dict[1], ref=reference_all_dict[0]["ref"])
        get_commit_dict = self.get_commit(user=split_dict[0], repo=split_dict[1], sha=reference_dict["object"]["sha"])
        tree_dict = self.create_tree(user=split_dict[0], repo=split_dict[1], base_tree=get_commit_dict["tree"]["sha"], path="README.md", gtype="blob", content=blob_dict)
        parents = [ reference_dict["object"]["sha"] ]
        commit_dict = self.create_commit(user=split_dict[0], repo=split_dict[1], message="creo readme.md", tree=tree_dict["sha"], parents=parents)
        return self.update_reference(user=split_dict[0], repo=split_dict[1], sha=commit_dict["sha"], ref=reference_dict["ref"])

    def create_orgfile(self, repository): 
        split_dict = repository.split("/")
        blob_dict = self.create_blob(user=split_dict[0], repo=split_dict[1], content=self.file_to_binary("static/repository/seample/project.org"))
        reference_all_dict = self.get_all_reference(user=split_dict[0], repo=split_dict[1])
        reference_dict = self.get_reference(user=split_dict[0], repo=split_dict[1], ref=reference_all_dict[0]["ref"])
        get_commit_dict = self.get_commit(user=split_dict[0], repo=split_dict[1], sha=reference_dict["object"]["sha"])
        tree_dict = self.create_tree(user=split_dict[0], repo=split_dict[1], base_tree=get_commit_dict["tree"]["sha"], path="project.org", gtype="blob", content=blob_dict)
        parents = [ reference_dict["object"]["sha"] ]
        commit_dict = self.create_commit(user=split_dict[0], repo=split_dict[1], message="creo project.org", tree=tree_dict["sha"], parents=parents)
        return self.update_reference(user=split_dict[0], repo=split_dict[1], sha=commit_dict["sha"], ref=reference_dict["ref"])

    def update_orgfile(self, repository, path):
        split_dict = repository.split("/")
        blob_dict = self.create_blob(user=split_dict[0], repo=split_dict[1], content=self.file_to_binary(path))
        reference_all_dict = self.get_all_reference(user=split_dict[0], repo=split_dict[1])
        reference_dict = self.get_reference(user=split_dict[0], repo=split_dict[1], ref=reference_all_dict[0]["ref"])
        get_commit_dict = self.get_commit(user=split_dict[0], repo=split_dict[1], sha=reference_dict["object"]["sha"])
        tree_dict = self.create_tree(user=split_dict[0], repo=split_dict[1], base_tree=get_commit_dict["tree"]["sha"], path="project.org", gtype="blob", content=blob_dict)
        parents = [ reference_dict["object"]["sha"] ]
        commit_dict = self.create_commit(user=split_dict[0], repo=split_dict[1], message="aggiorno project.org", tree=tree_dict["sha"], parents=parents)
        return self.update_reference(user=split_dict[0], repo=split_dict[1], sha=commit_dict["sha"], ref=reference_dict["ref"])
    
    #########
    # HOOKS
    #########

    # return a dict with the list of hooks 
    def list_hooks(self, user, repo): 
        json = self.get("repos/" + user + "/" + repo + "/hooks")
        return json 

    # creo l'hook impostando le notifica come push
    def create_hook(self, user, repo):
        if self.exist_hook(user=user, repo=repo): 

            data = {
                "name": "web",
                "active": True,
                "events": [
                    "push" # ,
                    # "pull_request"
                ],
                "config": {
                    "url": "http://tracktask.ngrok.io/payload",
                    "content_type": "json"
                  }
            }

            self.update_json(user=user, repo=repo)
            return self.post('repos/' + user + "/" + repo + '/hooks', data=data)
        return False


    # controllo l'esistenza dell' hook comparando url di destinazione
    def exist_hook(self, user, repo): 
        hooks_dict = self.list_hooks(user=user, repo=repo)

        flag = True 
        for hook in hooks_dict:
            if "http://tracktask.ngrok.io/payload".upper() in hook["config"]["url"].upper():
                flag = False
                pass 

        return flag