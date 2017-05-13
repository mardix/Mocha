from mocha.decorators import emit_signal

@emit_signal()
def create_user(change):
    """
    Emit a signal when a new user has been created
    Returns the USER instance
    """
    return change()

@emit_signal()
def user_update(user, action, change, data={}):
    """
    Emit when a user's account has been update. 
    Check action to see the type of update 

    :param user: The user instance
    :param action: the action taken
    :param change: a callback fn that will executed
    :param data: additional data 
    :return: a tuple (user, action, change)
    """
    return user, action, change()

@emit_signal()
def delete_user(change):
    """
    When a user has been deleted
    """
    return change()

@emit_signal()
def user_login(change):
    """
    Emit signal when logged in
    """
    return change()

@emit_signal()
def user_logout(change):
    """
    When logout
    """
    return change()


