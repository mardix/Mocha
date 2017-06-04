"""
Contact Page
"""
from mocha import (Mocha,
                   _,
                   config,
                   url_for,
                   abort,
                   request,
                   utils,
                   flash_success,
                   flash_error,
                   flash_data,
                   get_flash_data,
                   send_mail,
                   recaptcha,
                   page_attr,
                   redirect,
                   decorators as deco,
                   db,
                   render,
                   exceptions)

import mocha.contrib
import mocha.contrib.app_data as app_data

import logging

__version__ = "1.0.0"
__options__ = {}

APP_DATA_KEY = "contrib.contact-us"


class Main(Mocha):
    @classmethod
    def _register(cls, app, **kwargs):
        """ Reset some params """

        # nav
        nav = __options__.get("nav", {})
        nav.setdefault("title", "Contact")
        nav.setdefault("visible", True)
        nav.setdefault("order", 100)
        title = nav.pop("title")
        render.nav.add(title, cls.page, **nav)

        # route
        kwargs["base_route"] = __options__.get("route", "/contact/")

        # App Option
        data = {
            "recipients": __options__.get("recipients"),
            "success_message": __options__.get("success_message",
                                               "Message sent. Thanks!")
        }

        @app.before_first_request
        def setup():
            if db._IS_OK_:
                try:
                    app_data.set(APP_DATA_KEY, data, init=True)
                except Exception as ex:
                    logging.fatal("mocha.contrib.app_data has not been setup. Need to run `mocha :dbsync`")
                    abort(500)

        # Call the register
        super(cls, cls)._register(app, **kwargs)

    @request.route("/", methods=["GET", "POST"])
    @render.template("contrib/contact_us/Main/page.jade")
    def page(self):

        recipients = app_data.get(APP_DATA_KEY, "recipients") \
                     or __options__.get("recipients") \
                     or config("CONTACT_EMAIL")

        if not recipients:
            abort(500, "ContactPage missing email recipient")

        success_message = app_data.get(APP_DATA_KEY,
                                       "success_message",
                                       __options__.get("success_message"))

        return_to = __options__.get("return_to", None)
        if return_to:
            if "/" not in return_to:
                return_to = url_for(return_to)
        else:
            return_to = url_for(self)

        if request.method == "POST":
            email = request.form.get("email")
            subject = request.form.get("subject")
            message = request.form.get("message")
            name = request.form.get("name")

            try:
                if recaptcha.verify():
                    if not email or not subject or not message:
                        raise exceptions.AppError("All fields are required")
                    elif not utils.is_email_valid(email):
                        raise exceptions.AppError("Invalid email address")
                    else:
                        try:
                            send_mail(to=recipients,
                                      reply_to=email,
                                      mail_from=email,
                                      mail_subject=subject,
                                      mail_message=message,
                                      mail_name=name,
                                      template=__options__.get("template",
                                                               "contact-us.txt")
                                      )
                            flash_data("ContactPage:EmailSent")
                        except Exception as ex:
                            logging.exception(ex)
                            raise exceptions.AppError("Unable to send email")
                else:
                    raise exceptions.AppError("Security code is invalid")
            except exceptions.AppError as e:
                flash_error(e.message)
            return redirect(self)

        title = __options__.get("title", _("Contact Us"))
        page_attr(title)

        fd = get_flash_data()
        return {
            "title": title,
            "email_sent": True if fd and "ContactPage:EmailSent" in fd else False,
            "success_message": success_message,
            "return_to": return_to
        }


@render.nav("Contact Us")
@mocha.contrib.admin
class Admin(Mocha):
    @request.route("/contact")
    @render.nav("Settings")
    @render.template("contrib/contact_us/Admin/index.jade")
    def index(self):
        adata = app_data.get(APP_DATA_KEY)
        page_attr("Contact Us Settings")
        return {
            "recipients": adata.get("recipients"),
            "success_message": adata.get("success_message"),
        }

    def post(self):
        recipients = request.form.get("recipients")
        success_message = request.form.get("success_message")

        if not recipients or not success_message:
            flash_error("Missing 'recipients' or 'success message'")
        else:

            data = {
                "recipients": recipients,
                "success_message": success_message
            }
            app_data.set(APP_DATA_KEY, data)
            flash_success("Contact Us Settings saved")

        return redirect(self.index)
