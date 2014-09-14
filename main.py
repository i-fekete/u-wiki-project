import webapp2, \
	jinja2, \
	os, \
	re, \
	string, \
	random, \
	hashlib, \
	hmac, \
	logging, \
	urllib
from google.appengine.ext import db

#for making secure cookies
SECRET = 'somesecretstring'
ADMINS = ['fekete']

def is_profane(text):
	connection = urllib.urlopen('http://www.wdyl.com/profanity?q='+text)
	
	if 'true' in connection.read():
		profane = True
	else:
		profane = False
	
	connection.close()
	return profane


def make_secure_val(value):
	return '%s|%s' % (value, hmac.new(SECRET, value).hexdigest())

def check_secure_val(secure_val):
	value = secure_val.split('|')[0]
	if make_secure_val(value) == secure_val:
		return value

class Handler(webapp2.RequestHandler):
	#removed render_str function as it seemd to be unnecessary
	#moved template_dir and jinja_env variables inside render method
	
	def write(self, *args, **kwargs):
		self.response.out.write(*args, **kwargs)

	def render(self, template, **kwargs):
		template_dir = os.path.join(os.path.dirname(__file__), 'templates')
		jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape = True)
		template = jinja_env.get_template(template)
		
		self.write(template.render(**kwargs))

	def set_cookie(self, name, value):
		#this has been altered to handle logout here
		if value:
			cookie_value = make_secure_val(value)
		else:
			cookie_value = ''
			#if else added to avoid type error
		
		self.response.headers.add_header(
			'Set-Cookie',
			'%s=%s; Path=/' % (name, cookie_value))

	def read_cookie(self, name):
		cookie_value = self.request.cookies.get(name)
		return cookie_value and check_secure_val(cookie_value)

	def login(self, user):
		self.set_cookie('user_id', str(user.key().id()))

	def logout(self):
		self.set_cookie('user_id', '')

	def initialize(self, *args, **kwargs):
		webapp2.RequestHandler.initialize(self, *args, **kwargs)
		user_id = self.read_cookie('user_id')
		self.user = user_id and User.by_id(int(user_id))
		if self.user:
			self.header = {'signed_in': True,
						   'user_name': '%s' % (self.user.name)}
		else:
			self.header = {'signed_in': False}
		#self.header is passed over to the base.html


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


class User(db.Model):
	name = db.StringProperty(required = True)
	pw_hash = db.StringProperty(required = True)
	email = db.StringProperty()

	@classmethod
	def by_id(cls, uid):
		return cls.get_by_id(uid)

	@classmethod
	def by_name(cls, name):
		return cls.all().filter('name =', name).get()

	@classmethod
	def register(cls, name, password, email = None):
		pw_hash = make_pw_hash(name, password)
		return cls(name = name, pw_hash = pw_hash, email = email)

	@classmethod
	def login(cls, name, password):
		user = cls.by_name(name)
		if user and valid_login(name, password, user.pw_hash):
			return user


class SignupHandler(Handler):

	def get(self):
		self.render('signup.html', **self.header)

	def post(self):

		self.username = self.request.get('username')
		self.password = self.request.get('password')
		self.verification = self.request.get('verify')
		self.email = self.request.get('email')

		params = dict(username = self.username,
					  email = self.email)

		valid_len = len(params)
		#Instead of the have_error flag, to avoid forgetting to set the flag somewhere

		if not valid_username(self.username):
			params['error_username'] = 'Invalid username'
		elif User.by_name(self.username): #if user already exists in db
			params['error_username'] = 'User already exists'

		if not valid_password(self.password):
			params['error_password'] = 'Invalid password'
		elif self.password != self.verification:
			params['error_verification'] = 'Passwords did not match'

		if not valid_email(self.email):
			params['error_email'] = 'Invalid email'

		
		if len(params) != valid_len:
			#rerenders page if arguments (errors) have been added to params
			self.render('signup.html', **params)
		
		else:
			new_user = User.register(self.username, self.password, self.email)
			new_user.put()

			self.login(new_user)

			self.redirect('/')


class LoginHandler(Handler):

	def get(self):
		self.render('login.html', **self.header)

	def post(self):

		self.username = self.request.get('username')
		self.password = self.request.get('password')

		user = User.login(self.username, self.password)
		#logging.info(user)
		if user:
			self.login(user)
			self.redirect('/')
		else:
			self.render('login.html', login_error = "Invalid login")

class LogoutHandler(Handler):

	def get(self):
		self.logout()

		self.redirect('/')


class Wiki(db.Model):
	wiki_kw = db.StringProperty(required = True)
	text = db.TextProperty(required = True)
	date = db.DateTimeProperty(auto_now_add = True)

	@classmethod
	def by_wiki_kw(cls, wiki_kw):
		return cls.all().filter('wiki_kw =', wiki_kw).order('-date').get()
		#wiki_kw is actually the permalink


class EditHandler(Handler):
	
	def get(self, wiki_kw):

		if not self.user:
			self.redirect('/login')

		elif wiki_kw == '/' and self.user.name not in ADMINS:
			self.write('This page cannot be edited by visitors')

		else:
			post_id = self.request.get('post_id')

			if post_id:
				post_id = int(post_id[1:])
				post = Wiki.get_by_id(post_id)

			else:
				post = Wiki.by_wiki_kw(wiki_kw)

			if post:
				self.render('edit.html', wiki_kw = wiki_kw[1:], edit = True, text = post.text, **self.header)
				#edit is passed in for the base.html to check which links to display in the header
			else:
				self.render('edit.html', wiki_kw = wiki_kw[1:], **self.header)


	def post(self, wiki_kw):
		
		text = self.request.get('content')

		new_entry = Wiki(wiki_kw = wiki_kw, text = text)
		new_entry.put()

		self.redirect(wiki_kw)

#This approach did not work with input with html code
#		if not is_profane(text):
#			new_entry = Wiki(wiki_kw = wiki_kw, text = text)
#			new_entry.put()
#
#			self.redirect(wiki_kw)
#
#		else:
#			profanity_error = 'You seem to have used an inappropriate word (checked with www.wdyl.com)'
#			self.render('edit.html', wiki_kw = wiki_kw[1:], edit = True, text = text,
#			profanity_error = profanity_error, **self.header)
#

class HistoryHandler(Handler):
	
	def get(self, wiki_kw):

		if wiki_kw == '/' and self.user.name not in ADMINS:
			history = [Wiki.by_wiki_kw(wiki_kw)]

		else:
			history = Wiki.all().filter('wiki_kw =', wiki_kw).order('-date')
			history = list(history)

		self.render('history.html', wiki_kw = wiki_kw[1:], history = history, **self.header)
		#history is also used by base.html to determine if history or view links should be displayed in the header


class WikiHandler(Handler):
	
	def get(self, wiki_kw):
		
		post_id = self.request.get('post_id')

		if post_id:
			post_id = int(post_id[1:])
			post = Wiki.get_by_id(post_id)

		else:
			post = Wiki.by_wiki_kw(wiki_kw)

		if post:
			text = post.text#.replace('\n', '<br>')
			#uncomment above to allow proper line brakes in non-html posts
			self.render('wiki.html', wiki_kw = wiki_kw[1:], text = text, **self.header)
		else:
			self.redirect('/_edit%s' % (wiki_kw))
			

class IndexHandler(Handler):
	#an index of all the keywords
	def get(self):
		index_base = Wiki.all().order('wiki_kw')
		index_base = list(index_base)
		
		index = []

		for entry in index_base:
			keyword = entry.wiki_kw
			if keyword not in index:
				index.append(keyword)

		index.sort(key = lambda s: s.lower())

		self.render('index.html', index = index, **self.header)


class RedirectHandler(Handler):
	#This is to handle the edit and view links in the history for older posts
	def get(self, post_id):
		task = self.request.get('task')
		if task == 'view':
			task = ''
		wiki_kw = self.request.get('wiki_kw')
		self.redirect('%s%s?post_id=%s' % (task, wiki_kw, post_id))


PAGE_RE = r'(/(?:[a-zA-Z0-9_-]+/?)*)'
app = webapp2.WSGIApplication([
	('/login', LoginHandler),
	('/signup', SignupHandler),
	('/logout', LogoutHandler),
	('/index', IndexHandler),
	('/_redirect' + PAGE_RE, RedirectHandler),
	('/_edit' + PAGE_RE, EditHandler),
	('/_history' + PAGE_RE, HistoryHandler),
	(PAGE_RE, WikiHandler),
	], debug=True)