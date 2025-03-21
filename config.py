import os
from sqlalchemy import create_engine

import urllib

class Config(object):
    SECRET_KEY = "Clave unica"
    SESION_COOKIE_NAME = False

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:1234@localhost:3306/Examen'
    SQLALCHEMY_TRACK_MODIFICATIONS = False