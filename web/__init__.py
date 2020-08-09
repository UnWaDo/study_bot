from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import logging

app = Flask(__name__)
app.config.from_object('config')

db = SQLAlchemy(app)
logging.basicConfig(filename='app.log', filemode='a', format='%(asctime)s # %(message)s',
                                datefmt='%d-%b-%y, %H:%M:%S', level=logging.INFO)


import web.views
