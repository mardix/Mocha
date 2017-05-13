# Extensions

Extensions are some flask extensions that are already loaded in your application 
for you to use. They can be configured through their native configuration or 
through Mocha config.


---

## upload


---

## cache 

**cache** exposes a caching mechanism for your application's views.

    from mocha import cache

**Configuration**

    #: Flask-Cache is used to caching

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
    

**Example**

    class Index(Mocha):
        
        @cache.cached(60*60)
        def index(self):
            pass

 
Extension: [flask-cache](https://github.com/thadeusb/flask-cache)

---


## mail

**mail** exposes an interface to send email via SMTP or AWS SES.

 
    from mocha import mail

**Configuration**

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

**ReCaptcha** implements the Google recaptcha in your application. 

    from mocha import recaptcha
    

**Configuration**

    #: Flask-Recaptcha
    #: Register your application at https://www.google.com/recaptcha/admin

    #: RECAPTCHA_ENABLED
    RECAPTCHA_ENABLED = True

    #: RECAPTCHA_SITE_KEY
    RECAPTCHA_SITE_KEY = ""

    #: RECAPTCHA_SECRET_KEY
    RECAPTCHA_SECRET_KEY = ""

**Jinja Code**

To include the recaptcha in your template add the code below

    {{ recaptcha }}

**Verify Code**

    class Index(Mocha):
        
        def index(self):
            pass
            
        @post
        def send_data(self):
            if recaptcha.verify():
                # SUCCESS
            else:
                # FAILED
            
**About**

Extension: [flask-recaptcha](https://github.com/mardix/flask-recaptcha)

To register your application go [https://www.google.com/recaptcha/admin](https://www.google.com/recaptcha/admin)

---


## csrf 

**csrf** prevents cross-site request forgery (CSRF) on your application

    from mocha import csrf
    
Automatically all POST, UPDATE methods will require a CSRF token, unless explicitly exempt.

To exempt and endpoint, jus add the decorator `csrf.exempt`

    class Index(Mocha):
        
        def index(self):
            pass
            
        @post()
        @csrf.exempt
        def exempted_post(self):
            pass
            
        @post()
        def save_data(self):
            pass
            
In the example above, when posting to `/exempted-post/` it will not require the CSRF token,
however `/save-data/` requires it. 


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

    from mocha import storage

### Configuration

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






