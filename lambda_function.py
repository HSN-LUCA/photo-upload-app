import json
from flask import Flask
from application import application
import awsgi

def lambda_handler(event, context):
    return awsgi.response(application, event, context)