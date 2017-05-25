# -*- coding: utf-8 -*-
"""
Mocha

Views

"""
from mocha import (Mocha,
                   page_title,
                   get_config,
                   flash_success,
                   flash_error,
                   abort,
                   request,
                   url_for,
                   redirect,
                   models,
                   utils,
                   paginate,
                   decorators as deco
                   )


# ------------------------------------------------------------------------------


@deco.route("/%ROUTE%/")
@deco.nav_title("%NAV_TITLE%")
class Index(Mocha):

    @deco.nav_title("Home", order=1)
    def index(self):
        page_title("Hello View!")
        return
