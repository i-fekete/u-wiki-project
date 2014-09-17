import hmac, \
	hashlib, \
	random, \
	string, \
	re

SECRET = 'somesecretstring'

def make_secure_val(value):
	return '%s|%s' % (value, hmac.new(SECRET, value).hexdigest())

def check_secure_val(secure_val):
	value = secure_val.split('|')[0]
	if make_secure_val(value) == secure_val:
		return value

# regex for user input validation
USER_RE = re.compile(r'^[a-zA-Z0-9_-]{3,20}$')
def valid_username(username):
	return username and USER_RE.match(username)

PASS_RE = re.compile(r'^.{3,20}$')	
def valid_password(password):
	return password and PASS_RE.match(password)

EMAIL_RE  = re.compile(r'^[\S]+@[\S]+\.[\S]+$')	
def valid_email(email):
	return not email or EMAIL_RE.match(email)


#login
def make_salt(length = 5):
	return ''.join(random.choice(string.letters) for n in xrange(length))

def make_pw_hash(name, password, salt = None):
	if not salt:
		salt = make_salt()
	hashed = hashlib.sha256(name + password + salt).hexdigest()
	return '%s,%s' %(salt, hashed)

def valid_login(name, password, pw_hash):
	salt = pw_hash.split(',')[0]
	return pw_hash == make_pw_hash(name, password, salt)


#this is a profanity checker to be implemented
#def is_profane(text):
#	connection = urllib.urlopen('http://www.wdyl.com/profanity?q='+text)
#	
#	if 'true' in connection.read():
#		profane = True
#	else:
#		profane = False
#	
#	connection.close()
#	return profane