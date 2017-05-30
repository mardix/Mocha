# -*- coding: utf-8 -*-
""""
________________________________________________________________________________
MOCHA: https://github.com/mardix/mocha
________________________________________________________________________________
"""

from mocha import Brew

# == CLI ==
# Import your app manager. Omit if it will not be used
import application.manage


# == PROJECTS ==
# Apps is a dict with list of views that will be loaded by name
# ie: `app=main mocha :serve` will serve all the views in the `main` list
# Views are placed in application/views directory, and should be listed as string
# without the `.py`
# You can add as many projects as you want, containing as many views
# It also allows you to use multiple config env
# ie: `app=main:production mocha :serve` will use the `main` project with
# `production` config

apps = {
    "main": [
        "main"
    ]
}

# == INIT ==
# Init the application
# 'app' variable is mandatory if you plan on using the mocha cli
app = Brew(__name__, apps)

