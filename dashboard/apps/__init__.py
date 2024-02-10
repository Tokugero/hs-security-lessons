# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

import os
import shutil

from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from importlib import import_module
from apps import authentication
from git import Repo

db = SQLAlchemy()
login_manager = LoginManager()

def register_extensions(app):
    db.init_app(app)
    login_manager.init_app(app)


def register_blueprints(app):
    for module_name in ('authentication', 'home'):
        module = import_module('apps.{}.routes'.format(module_name))
        app.register_blueprint(module.blueprint)


def configure_database(app):

    @app.before_first_request
    def initialize_database():
        try:
            db.create_all()
        except Exception as e:

            print('> Error: DBMS Exception: ' + str(e) )

            # fallback to SQLite
            app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI = 'sqlite:////config/db.sqlite3'

            print('> Fallback to SQLite ')
            db.create_all()

        # Create first admin user
        try:
            teacher = authentication.models.Users(id=1, username="teacher", email="te@ch.er", password=os.getenv('TEACHERPASS', 'adminadmin'), role="teacher")
            db.session.add(teacher)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            pass

    @app.teardown_request
    def shutdown_session(exception=None):
        db.session.remove() 


def create_app(config):
    app = Flask(__name__)
    app.config.from_object(config)
    register_extensions(app)
    register_blueprints(app)
    configure_database(app)
    return app

def global_pull():
    try:
        repo = Repo.clone_from(os.getenv("LESSONREPO", "git@192.168.128.102:teacher/lessons.git") , "/tmp/lessons", branch="main")
    except Exception as e:
        repo = Repo("/tmp/lessons").remote().pull()

    # Clean the static asset folder
    shutil.rmtree("/apps/static/assets/lessons")
    
    # Repopulate the static asset folder
    lessons = os.listdir("/tmp/lessons/lessons")
    for lesson in lessons:
        if os.path.isdir("/tmp/lessons/lessons/"+lesson+"/assets"):
            shutil.copytree("/tmp/lessons/lessons/"+lesson+"/assets", "/apps/static/assets/lessons/"+lesson+"/assets")