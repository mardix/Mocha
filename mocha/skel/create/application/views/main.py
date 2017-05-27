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
                   decorators as deco
                   )


# ------------------------------------------------------------------------------


class Index(Mocha):

    @deco.nav_title("Home", order=1)
    def index(self):
        page_attr(title="Hello View!")
        return
