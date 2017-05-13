"""
views.admin is a basic home page for your admin area
"""

from mocha import (Mocha,
                   decorators as deco,
                   )

import mocha.contrib


@deco.route("/admin/")
@mocha.contrib.admin
class Admin(Mocha):

    @deco.template("contrib/admin/Admin/index.jade")
    @deco.nav_title("Admin Home", tags=mocha.contrib.ADMIN_TAG,
                    attach_to=["mocha.contrib.views.auth.Account", "self"])
    def index(self):
        return
