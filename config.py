import os

class Config(object):
    #SECRET_KEY = os.environ.get('SECRET_KEY')
    SECRET_KEY = "Thisisasecret"
    TOKEN_TIMEOUT = 30      #specified in minutes
    MYSQL_DATABASE_USER = os.environ['MYSQL_USER']
    MYSQL_DATABASE_PASSWORD = os.environ['MYSQL_PASSWORD']
    MYSQL_DATABASE_DB = os.environ['MYSQL_DB']
    MYSQL_DATABASE_HOST = os.environ['MYSQL_HOST']
    