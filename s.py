
from mocha import bcrypt
s = "hello-world"
h = bcrypt.hash(s)
print(h, bcrypt.verify(s, h))


