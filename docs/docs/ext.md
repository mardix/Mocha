# Extensions

Extensions are some flask extensions that are already loaded in your application 
for you to use. They can be configured through their native configuration or 
through Mocha config.

---

## bcrypt

`bcrypt` from the `passlib` library is used to hash and verify password.


#### Import

    from mocha import bcrypt

#### Hash password

Hash a password for storage

    my_string_pass = "mypass123"
    my_hash = bcrypt.hash(my_string_pass)

#### Verify password

Verify a password by using the string provided to hash, and the hash that was created previously. It returns a bool.

    bcrypt.verify(my_string_pass, my_hash)


#### Config

`bcrypt` can be used with no configuration as it will fall back to its default. But if you want you can have the following
config

    BCRYPT_SALT = ""

    BCRYPT_ROUNDS = 12

    BCRYPT_INDENT = ""


---


## cache 

`flask_cache` is used to cache data. It allows to use different backend, ie: Redis, Memcache, etc.


#### Import

    from mocha import cache


#### Decorator

    from mocha import Mocha, cache

    class Index(Mocha):

        @cache.cached(3600)
        def index(self):
            return {

            }


#### Config

    #: CACHE_TYPE
    #: The type of cache to use
    #: null, simple, redis, filesystem,
    CACHE_TYPE = "simple"

    #: CACHE_REDIS_URL
    #: If CHACHE_TYPE is 'redis', set the redis uri
    #: redis://username:password@host:port/db
    CACHE_REDIS_URL = ""

    #: CACHE_DIR
    #: Directory to store cache if CACHE_TYPE is filesystem, it will
    CACHE_DIR = ""

 
Extension: [flask-cache](https://github.com/sh4nks/flask-caching)

---


## mail

Mail exposes an interface to send email via SMTP or AWS SES.


#### Import

    from mocha import send_mail

#### Send Mail

Send mail helps you quickly send emails.

    template = ""
    to = "me@email.com"

    send_email(template=template, to=to)

#### Mail signals observer

    from mocha import signals

    @signals.send_email.observe
    def my_email_observer():
        pass


#### Mail interface

    from mocha.ext import mail


#### Config

    # AWS SES
    # To use AWS SES to send email
    #:
    #: - To use the default AWS credentials (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
    #: set MAIL_URI = "ses://"
    #: * To use a different credential:
    #: set MAIL_URI = "ses://{access_key}:{secret_key}@{region}"
    #:
    #: *** uncomment if you are using SMTP instead
    MAIL_URI = "ses://"

    # SMTP
    #: If you are using SMTP, it will use Flask-Mail
    #: The uri for the smtp connection. It will use Flask-Mail
    #: format: smtp://USERNAME:PASSWORD@HOST:PORT
    #: with sll -> smtp+ssl://USERNAME:PASSWORD@HOST:PORT
    #: with ssl and tls -> smtp+ssl+tls://USERNAME:PASSWORD@HOST:PORT
    #:
    #: *** comment out if you are using SES instead
    # MAIL_URI = "smtp+ssl://{username}:{password}@{host}:{port}"\
    #    .format(username="", password="", host="smtp.gmail.com", port=465)

    #: MAIL_SENDER - The sender of the email by default
    #: For SES, this email must be authorized
    MAIL_SENDER = APPLICATION_ADMIN_EMAIL

    #: MAIL_REPLY_TO
    #: The email to reply to by default
    MAIL_REPLY_TO = APPLICATION_ADMIN_EMAIL

    #: MAIL_TEMPLATE
    #: a directory that contains the email template or a dict
    MAIL_TEMPLATE = os.path.join(APPLICATION_DATA_DIR, "mail-templates")

    #: MAIL_TEMPLATE_CONTEXT
    #: a dict of all context to pass to the email by default
    MAIL_TEMPLATE_CONTEXT = {
        "site_name": APPLICATION_NAME,
        "site_url": APPLICATION_URL
    }
    
    
As a convenience, you can use `send_email()` to send email. 

    from mocha import Mocha, send_email

    class Index(Mocha):
        
        @post()
        def send():
            recipient = "email@email.com"
            sender = request.form.get("sender")
            subject = "Welcome"
            
            mail.send(to=recipient, sender=sender, subject=subet)
            
            
Extension: [ses-mailer](https://github.com/mardix/ses-mailer)

Extension: [flask-mail](https://github.com/mattupstate/flask-mail)



---

## recaptcha 

Recaptcha implements the Google recaptcha in your application.

#### Import

    from mocha import recaptcha
    

#### Implement in Jinja

To include the recaptcha in your template add the code below

    {{ recaptcha }}


#### Verify code


    class Index(Mocha):

        def send_data(self):
            if recaptcha.verify():
                # everythings is ok
            else:
                # FAILED


#### Config

    #: Flask-Recaptcha
    #: Register your application at https://www.google.com/recaptcha/admin

    #: RECAPTCHA_ENABLED
    RECAPTCHA_ENABLED = True

    #: RECAPTCHA_SITE_KEY
    RECAPTCHA_SITE_KEY = ""

    #: RECAPTCHA_SECRET_KEY
    RECAPTCHA_SECRET_KEY = ""


Extension: [flask-recaptcha](https://github.com/mardix/flask-recaptcha)

To register your application go [https://www.google.com/recaptcha/admin](https://www.google.com/recaptcha/admin)

---


## csrf

**csrf** prevents cross-site request forgery (CSRF) on your application

#### Import

    from mocha import csrf


Automatically all POST, UPDATE methods will require a CSRF token, unless explicitly exempt.

To exempt and endpoint, jus add the decorator `csrf.exempt`

    class Index(Mocha):
        
        def index(self):
            pass

        @csrf.exempt
        def exempted_post(self):
            pass
            
        @post()
        def save_data(self):
            pass
            
In the example above, when posting to `/exempted-post/` it will not require the CSRF token,
however `/save-data/` requires it. 



#### Config

        CSRF_COOKIE_NAME  # _csrf_token
        CSRF_HEADER_NAME  # X-CSRFToken
        CSRF_DISABLE
        CSRF_COOKIE_TIMEOUT
        CSRF_COOKIE_SECURE
        CSRF_COOKIE_HTTPONLY
        CSRF_COOKIE_DOMAIN
        CSRF_CHECK_REFERER
        SEASURF_INCLUDE_OR_EXEMPT_VIEWS


**About**
    
Extension: [flask-seasurf](https://github.com/maxcountryman/flask-seasurf)

SeaSurf is a Flask extension for preventing cross-site request forgery (CSRF).

CSRF vulnerabilities have been found in large and popular sites such as YouTube. 
These attacks are problematic because the mechanism they use is relatively easy to exploit. 
This extension attempts to aid you in securing your application from such attacks.


---


## session 

    from mocha import session


--

## storage

Allows you to to access, upload, download, save and delete files on cloud
storage providers such as: AWS S3, Google Storage, Microsoft Azure,
Rackspace Cloudfiles, and even Local file system

#### Import

    from mocha import storage


#### Upload File


#### Delete File


#### Config

Edit the keys below in your config class file:

    #: STORAGE_PROVIDER:
    # The provider to use. By default it's 'LOCAL'.
    # You can use:
    # LOCAL, S3, GOOGLE_STORAGE, AZURE_BLOBS, CLOUDFILES
    STORAGE_PROVIDER = "LOCAL"

    #: STORAGE_KEY
    # The storage key. Leave it blank if PROVIDER is LOCAL
    STORAGE_KEY = AWS_ACCESS_KEY_ID

    #: STORAGE_SECRET
    #: The storage secret key. Leave it blank if PROVIDER is LOCAL
    STORAGE_SECRET = AWS_SECRET_ACCESS_KEY

    #: STORAGE_REGION_NAME
    #: The region for the storage. Leave it blank if PROVIDER is LOCAL
    STORAGE_REGION_NAME = AWS_REGION_NAME

    #: STORAGE_CONTAINER
    #: The Bucket name (for S3, Google storage, Azure, cloudfile)
    #: or the directory name (LOCAL) to access
    STORAGE_CONTAINER = os.path.join(APPLICATION_DATA_DIR, "uploads")

    #: STORAGE_SERVER
    #: Bool, to serve local file
    STORAGE_SERVER = True

    #: STORAGE_SERVER_URL
    #: The url suffix for local storage
    STORAGE_SERVER_URL = "files"



### storage.get

Allows you to get a file from the storage

    my_file = storage.get("myfile.jpg")

    my_file.name  # return The file name

    my_file.size  # returns file size


### storage.upload






