import os

class Configuration(object):
    DEBUG = True

    APPLICATION_DIR = os.path.dirname(os.path.realpath(__file__))
    SECRET_KEY = '\xfd{H\xe5<\x95\xf9\xe3\x96.5\xd1\x01O<!\xd5\xa2\xa0\x9fR"\xa1\xa8'

    DOMINIO = "http://tracktask.ngrok.io"

    #github-flask
    GITHUB_CLIENT_ID = 'd10f825f5b61b54752ed'
    GITHUB_CLIENT_SECRET = '54465ae0579b34fe9f64a538391aa17cb5a35977'

    # For GitHub Enterprise
    GITHUB_BASE_URL = 'https://api.github.com/'
    GITHUB_AUTH_URL = 'https://github.com/login/oauth/'

    # flask-Mail configuration
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_SSL = False
    MAIL_USE_TLS = True
    MAIL_USERNAME = "tracktask2016@gmail.com"
    MAIL_PASSWORD = "6p9-fAA-YnT-T7C"
    MAIL_DEFAULT_SENDER = "tracktask2016@gmail.com"