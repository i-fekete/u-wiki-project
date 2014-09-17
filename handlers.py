import webapp2, \
	jinja2, \
	os, \
	logging

from utils import *
from dbs import *

ADMINS = ['fekete']

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

		key = 'index'
		index = memcache.get(key)
		if not index:
			index = db.GqlQuery("SELECT DISTINCT wiki_kw FROM Wiki").run()#.order('wiki_kw')
			index = list(index)
			#index_base = list(index_base)
			
			#index = []

			#for entry in index_base:
			#	keyword = entry.wiki_kw
			#	if keyword not in index:
			#		index.append(keyword)

			#logging.error('Duplicate index entry')
			

		else:
			index.append(wiki_kw)
		memcache.set(key, index)		

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

		if wiki_kw == '/' and (not self.user or self.user.name not in ADMINS):
			history = [Wiki.by_wiki_kw(wiki_kw)[0]] #history html expects to get a list
			#this is to ensure that the '/' page history cannot be viewed by others than the admins
			#users not signed in or not admins view only the last page
			#this should be changed to display an error message without redirecting to a short history page

		else:
			history = Wiki.by_wiki_kw(wiki_kw)

		self.render('history.html', wiki_kw = wiki_kw[1:], history = history, **self.header)
		#history is also used by base.html to determine if history or view links should be displayed in the header


class WikiHandler(Handler):
	
	def get(self, wiki_kw):
		
		post_id = self.request.get('post_id')

		if post_id:
			post_id = int(post_id[1:])
			post = Wiki.get_by_id(post_id)
			#this should be served from memcache

		else:
			all_posts = Wiki.by_wiki_kw(wiki_kw)
			# lesson learned here: do not use direct indexing if object might not exist
			#post = Wiki.by_wiki_kw(wiki_kw)[0] is a bad idea

		if all_posts:
			post = all_posts[0]
			text = post.text#.replace('\n', '<br>')
			#uncomment above to allow proper line brakes in non-html posts
			self.render('wiki.html', wiki_kw = wiki_kw[1:], text = text, **self.header)
		else:
			self.redirect('/_edit%s' % (wiki_kw))
			

class IndexHandler(Handler):
	#an index of all the keywords
	def get(self):
		key = 'index'
		index = memcache.get(key)

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

