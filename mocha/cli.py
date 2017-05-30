# -*- coding: utf-8 -*-
"""
________________________________________________________________________________

 /$$   /$$                                            /$$
| $$  | $$                                           | $$
| $$  | $$  /$$$$$$   /$$$$$$  /$$$$$$  /$$$$$$/$$$$ | $$$$$$$   /$$$$$$
| $$$$$$$$ |____  $$ /$$__  $$|____  $$| $$_  $$_  $$| $$__  $$ /$$__  $$
| $$__  $$  /$$$$$$$| $$  \__/ /$$$$$$$| $$ \ $$ \ $$| $$  \ $$| $$$$$$$$
| $$  | $$ /$$__  $$| $$      /$$__  $$| $$ | $$ | $$| $$  | $$| $$_____/
| $$  | $$|  $$$$$$$| $$     |  $$$$$$$| $$ | $$ | $$| $$$$$$$/|  $$$$$$$
|__/  |__/ \_______/|__/      \_______/|__/ |__/ |__/|_______/  \_______/



https://github.com/mardix/mocha

________________________________________________________________________________
"""

import os
import re
import sys
import traceback
import logging
import importlib
import pkg_resources
import click
import yaml
import functools
import json
from werkzeug import import_string
from .__about__ import *
from mocha import utils
import flask
import sh
import subprocess
from .core import db


CWD = os.getcwd()
SKELETON_DIR = "skel"
APPLICATION_DIR = "%s/application" % CWD


class Manager(object):
    """
    For command line classes in which __init__ contains all the functions to use

    example

    class Manager(cli.Manager):
        def __init__(self, command, click):

            @command()
            def hello():
                click.echo("Hello world")

            @command()
            @click.argument("name")
            def say_my_name(name):
                click.echo("My name is %s" % name)
    """
    pass


def get_project_dir_path(project_name):
    return "%s/%s" % (APPLICATION_DIR, project_name)


def copy_resource_dir(src, dest):
    """
    To copy package data directory to destination
    """
    package_name = "mocha"
    dest = (dest + "/" + os.path.basename(src)).rstrip("/")
    if pkg_resources.resource_isdir(package_name, src):
        if not os.path.isdir(dest):
            os.makedirs(dest)
        for res in pkg_resources.resource_listdir(__name__, src):
            copy_resource_dir(src + "/" + res, dest)
    else:
        if not os.path.isfile(dest) and os.path.splitext(src)[1] not in [".pyc"]:
            copy_resource_file(src, dest)


def copy_resource_file(src, dest):
    with open(dest, "wb") as f:
        f.write(pkg_resources.resource_string(__name__, src))

# ------------------------------------------------------------------------------
application = None


def run_cmd(cmd):
    subprocess.call(cmd.strip(), shell=True)


def get_propel_config(cwd, key):
    with open("%s/%s" % (cwd, "propel.yml")) as f:
        config = yaml.load(f)
    return config.get(key)


# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
def catch_exception(func):
    @functools.wraps(func)
    def decorated_view(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except Exception as ex:
            print("-" * 80)
            print("Exception Uncaught")
            print("-" * 80)
            print(ex)
            print("-" * 80)
    return decorated_view


def cwd_to_sys_path():
    sys.path.append(CWD)


def project_name(name):
    return re.compile('[^a-zA-Z0-9_]').sub("", name)


def header(title=None):
    print(__doc__)
    print("v. %s" % __version__)
    print("_" * 80)
    if title:
        print("** %s **" % title)


def build_assets(app):
    from webassets.script import CommandLineEnvironment
    assets_env = app.jinja_env.assets_environment
    log = logging.getLogger('webassets')
    log.addHandler(logging.StreamHandler())
    log.setLevel(logging.DEBUG)
    cmdenv = CommandLineEnvironment(assets_env, log)
    cmdenv.build()


@click.group()
def cli():
    """ Mocha (http://mardix.github.io/mocha) """


@cli.command(":init")
@catch_exception
def init():
    """  Setup Mocha in the current directory """

    mochapyfile = os.path.join(os.path.join(CWD, "brew.py"))

    header("Initializing Mocha ...")
    if os.path.isfile(mochapyfile):
        print("WARNING: It seems like Mocha is already setup!")
        print("*" * 80)
    else:
        print("")
        print("Copying files to the current directory...")
        copy_resource_dir(SKELETON_DIR + "/create/", CWD)
        print("")

        _npm_install_static()
        print("")
        print("----- Your Mocha is ready! ----")
        print("")
        print("> What's next?")
        print("- Edit the config [ application/config.py ] ")
        print("- If necessary setup your model database [ mocha :initdb ]")
        print("- Launch app on development mode, run [ mocha :serve ]")
        print("")
        print("*" * 80)


@cli.command(":addview")
@click.argument("name")
@click.option("--no-template", "-t", is_flag=True, default=False)
def add_view(name, no_template):
    """ Create a new view and template page """

    app_dest = APPLICATION_DIR
    viewsrc = "%s/create-view/view.py" % SKELETON_DIR
    tplsrc = "%s/create-view/template.jade" % SKELETON_DIR
    viewdest_dir = os.path.join(app_dest, "views")
    viewdest = os.path.join(viewdest_dir, "%s.py" % name)
    tpldest_dir = os.path.join(app_dest, "templates/%s/Index" % name)
    tpldest = os.path.join(tpldest_dir, "index.jade")

    header("Adding New View")
    print("View: %s" % viewdest.replace(CWD, ""))
    if not no_template:
        print("Template: %s" % tpldest.replace(CWD, ""))
    else:
        print("* Template will not be created because of the flag --no-template| -t")
    if os.path.isfile(viewdest) or os.path.isfile(tpldest):
        print("*** ERROR: View or Template file exist already")
    else:
        if not os.path.isdir(viewdest_dir):
            utils.make_dirs(viewdest_dir)
        copy_resource_file(viewsrc, viewdest)
        with open(viewdest, "r+") as vd:
            content = vd.read()\
                .replace("%ROUTE%", name.lower())\
                .replace("%NAV_TITLE%", name.capitalize())
            vd.seek(0)
            vd.write(content)
            vd.truncate()

        if not no_template:
            if not os.path.isdir(tpldest_dir):
                utils.make_dirs(tpldest_dir)
            copy_resource_file(tplsrc, tpldest)

    print("")
    print("*" * 80)


@cli.command(":serve")
@click.option("--port", "-p", default=5000)
@catch_exception
def server(port):
    """ Serve application in development mode """

    header("Serving application in development mode ... ")
    print("")
    print("- Port: %s" % port)
    print("")
    cwd_to_sys_path()
    application.app.run(debug=True, host='0.0.0.0', port=port)


@cli.command(":initdb")
def initdb():
    """ Sync database Create new tables etc... """

    print("Syncing up database...")
    cwd_to_sys_path()
    if db and hasattr(db, "Model"):
        db.create_all()
        for m in db.Model.__subclasses__():
            if hasattr(m, "initialize__"):
                print("Sync up model: %s ..." % m.__name__)
                getattr(m, "initialize__")()

    print("Done")


def _set_flask_alembic():
    from flask_alembic import Alembic

    """ Add the SQLAlchemy object in the global extension """
    application.app.extensions["sqlalchemy"] = type('', (), {"db": db})
    alembic = Alembic()
    alembic.init_app(application.app)
    return alembic



#@cli.command(":dbmigrate")
def db_migrate():
    """Migrate DB """
    print("Not ready for use")
    exit()
    cwd_to_sys_path()
    alembic = _set_flask_alembic()
    with application.app.app_context():
        p = db.Model.__subclasses__()
        print(p)

        # Auto-generate a migration
        alembic.revision('making changes')

        # Upgrade the database
        alembic.upgrade()


@cli.command(":assets2s3")
@catch_exception
def assets2s3():
    """ Upload assets files to S3 """
    import flask_s3

    header("Assets2S3...")
    print("")
    print("Building assets files..." )
    print("")
    build_assets(application.app)
    print("")
    print("Uploading assets files to S3 ...")
    flask_s3.create_all(application.app)
    print("")


@cli.command(":version")
def version():
    print("-" * 80)
    print(__version__)
    print("-" * 80)

# @cli.command("babel-build")
# def babelbuild():
#     print("Babel Build....")
#     #sh.pybabel()

def _npm_install_static():
    print("NPM Install packages...")
    static_path = os.path.join(CWD, "application/static")
    package_json = os.path.join(static_path, "package.json")

    try:
        if os.path.isfile(package_json):
            with sh.pushd(static_path):
                sh.npm("install", "-f")
        else:
            print("**ERROR: Can't install static files, `package.json` is missing at `%s`" % package_json)
            print("*" * 80)
    except sh.CommandNotFound as e:
        print("")
        print("*** Error Command Not Found: `{0}` is not found. You need to install `{0}` to continue".format(str(e)))
        print("*" * 80)

@cli.command(":install-assets")
def install_static():
    """ Install NPM Packages for the front end in the /static/ dir"""
    _npm_install_static()


# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------

def cmd():
    """
    Help to run the command line
    :return:
    """
    global application

    mochapyfile = os.path.join(os.path.join(CWD, "brew.py"))
    if os.path.isfile(mochapyfile):
        cwd_to_sys_path()
        application = import_string("brew")
    else:
        print("-" * 80)
        print("** Missing << 'brew.py' >> @ %s" % CWD)
        print("-" * 80)

    [cmd(cli.command, click) for cmd in Manager.__subclasses__()]
    cli()
