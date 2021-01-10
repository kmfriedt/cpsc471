from flask import Blueprint, request, jsonify
from api import mysql
import os

# all endpoint under schedule Blueprint share common url root of /
# endpoints in this file are only used for experimenting with the flask framework, not used for evaluation/demo
main = Blueprint('main', __name__)

#This file can be used for practice if you want. It's not needed for the project
@main.route("/")
@main.route("/home", methods = ['GET'])
def home():
	return "<p>Please see the <a href='https://documenter.getpostman.com/view/10336199/Szf6WoLL?version=latest'>Postman Documentation</a> for instruction on how to use the API </p>"



@main.route("/about/<name>")
def hello_name(name):
	return "Hello {}!".format(name)
	
