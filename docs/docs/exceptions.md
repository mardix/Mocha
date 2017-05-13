

# Exceptions

Mocha exposes some Error

## MochaError

**MochaError** is raised when there is an error in the core of Mocha


## AppError

**AppError** is an exception that is recommended to be used in your application. 


    class Index(Mocha):
        
        def error(self):
            try:
                # blah blah code
                raise AppError('Something bad happened..')
            except AppError as ae:
                flash_error(ae.message)


## ModelError



