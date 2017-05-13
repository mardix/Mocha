
class AuthError(Exception): pass
class LoginError(AuthError): pass
class SecureLoginError(AuthError): pass
class InvalidLoginError(LoginError): pass
class InvalidLoginPassword(LoginError): pass
class VerifyEmailError(LoginError): pass
