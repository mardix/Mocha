# -*- coding: utf-8 -*-
"""
Mocha

Views

"""
from mocha import (Mocha,
                   page_attr,
                   config,
                   flash_success,
                   flash_error,
                   abort,
                   request,
                   url_for,
                   redirect,
                   models,
                   utils,
                   paginate,
                   render,
                   decorators as deco
                   )


# ------------------------------------------------------------------------------


@request.route("/%ROUTE%/")
@render.nav_title("%NAV_TITLE%")
class Index(Mocha):

    @render.nav("Home", order=1)
    def index(self):
        page_attr(title="Hello View!")
        return
