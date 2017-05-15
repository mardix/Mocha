# -*- coding: utf-8 -*-
# Mocha

import os

# ------------------------------------------------------------------------------
# A convenient utility to access data path from your application and config files

# The application directory
# /apps
APP_DIR = os.path.dirname(__file__)

# The root dir
# /
ROOT_DIR = os.path.dirname(APP_DIR)

# Data directory
# apps/var
VAR_DIR = os.path.join(APP_DIR, "var")


def get_var_path(path):
    """
    get the path stored in the 'app/data' directory
    :param path: string
    :return: string
    """
    return os.path.join(VAR_DIR, path)



# ------------------------------------------------------------------------------

OAUTH_CREDENTIALS = {
    "facebook": {

    },
    "twitter": {

    },
    "google": {

    }
}



# ------------------------------------------------------------------------------
#
# AVAILABLE APPS
# Dict of available apps to be used in your app config
# To activate apps, just place each one of them in the
# INSTALLED_APPS config. ie
#
# INSTALLED_APPS = [
#     AVAILABLE_APPS["ERROR_PAGE"],
#     AVAILABLE_APPS["AUTH"],
#     ...
# ]
#
# The order is important. If an app depends on another app to work
# that must be placed before the calling app.
#
# Multiple app config of the same app can also be set to be used by different
# app. ie:
#
# AVAILABLE_APPS = {
#     "AUTH_ADMIN": "string.of.module.path", # string
#     "AUTH_WWW": ("string.of.module.path", {options.dict}), # tuple of (string, dict)
#     "MULTIPLE": [ # list of multiple tuples
#           ("string.of.module.path", {options.dict}),
#           ("string.of.module.path", {options.dict}),
# }
#
#
# INSTALLED_APPS = [
#     AVAILABLE_APPS["AUTH_WWW"],
#     ...
# ]
#
#

AVAILABLE_APPS = {
    # Error Page. Create a friendly page when an error occurs
    "ERROR_PAGE": "mocha.contrib.views.error_page",

    # ADMIN: for the admin section
    "ADMIN": ("mocha.contrib.views.admin", {
        "route": "/"
    }),

    # Maintenance page. When uncommented, the whole site will
    # show a maintenance page
    "MAINTENANCE_PAGE": ("mocha.contrib.views.maintenance_page", {
            "on": False,
            "exclude": []  # List of urls to exclude
        }
    ),

    # CONTACT PAGE: Creates a page for users to contact admin.
    # MAIL_* config must be setup
    "CONTACT_PAGE": (
        "mocha.contrib.views.contact_page",
        {
            "route": "/contact/",
            "nav": {
                "title": "Contact",
                "visible": True,
                "order": 100
            },
            "title": "Contact Us",
            "return_to": "main.Index:index",
            "recipients": "",
            "template": "contact-us.txt",
            "success_message": "Thank you for sending this message. "
                               "We'll contact you within the next 72 hours"
        }
    ),

    # AUTH: Authentication system to signup, login, manage users,
    # give access etc
    # Require to run `mocha syncdb` to setup the db
    # Also, run once `mochacli auth:create-super-admin email@xyz.com` to
    # create the super admin
    "AUTH": [
        ("mocha.contrib.views.auth", {

            # LOGIN MANAGER
            # Page to redirect to after login, if a ?next= is not provided
            "login_view": "main.Index:index",
            # Page to redirect to after user logout
            "logout_view": "main.Index:index",
            # Logging message, a message telling the user to login
            "login_message": "Please log in to access this page.",
            # Message category
            "login_message_category": "info",


            # PERMISSION
            # To allow user registration
            "allow_register": True,
            # To allow user login
            "allow_login": True,
            # Way to login/signup: email | oauth
            "allow_auth_methods": ["email", "oauth"],
            # Dict of OAuth credentials
            "oauth_credentials": OAUTH_CREDENTIALS,


            # USER VERIFICATION
            # Verify email on signup
            "verify_email": False,

            "verify_email_token_ttl": 60 * 24,
            "verify_email_template": "verify-email.txt",
            "verify_signup_email_template": "verify-signup-email.txt",

            # RESET PASSWORD
            "reset_password_method": "token",  # token or password
            "reset_password_token_ttl": 60,  # in minutes
            "reset_password_email_template": "reset-password.txt",

            # VIEWS
            # Login view: to login/logout/signup/lost-password
            "login": {
                # Base route
                "route": "/",
                # Nav
                "nav": {
                    "title": "Account"
                }
            },
            # User account, for the current user
            "account": {
                # The base route
                "route": "/account/",
                # Nav
                "nav": {
                    "title": "My Account"
                },

                # Custom Nav Title
                # Bool to format
                "set_custom_nav_title": False,
                # Way to customize the nav title
                # {USER_PROFILE_IMAGE_URL}: Will show the profile pic, add class 'img-circle' to make a circle image
                # {USER_NAME}: The user name
                # {USER_EMAIL}: The user email
                "custom_nav_title": "<img src='{USER_PROFILE_IMAGE_URL}' width=24 height=24 class='img-circle' /> <strong>{USER_NAME}</strong>",
            },
            # To admin users. Only managers can access this page
            "admin": {
                # Set to False to disable this section
                "enabled": True,
                # The base route
                "route": "/admin/users/",
                # Nav
                "nav": {
                    "title": "Users Admin"
                }
            }
        })
    ]
}
