import os

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or "Clave_unica_secreta"
    SESION_COOKIE_NAME = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:1234@localhost:3306/Examen'