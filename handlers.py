import webapp2, \
	jinja2, \
	os, \
	logging

from utils import *
from dbs import *

class Handler(webapp2.RequestHandler):
	#removed render_str function as it seemd to be unnecessary
	#moved template_dir and jinja_env variables inside render method
	
	def write(self, *args, **kwargs):
		self.response.out.write(*args, **kwargs)

	def render(self, template, **kwargs):
		template_dir = os.path.join(os.path.dirname(__file__), 'templates')
		jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape = True)
		template = jinja_env.get_template(template)

		kwargs['user2'] = self.user
		#this is to test if this works, should be made use of
		
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

	# def get_last_post(self, wiki_kw):
	# 	post_id = self.request.get('post_id')

	# 	if post_id:
	# 		post_id = int(post_id[1:])
	# 		post = Wiki.get_by_id(post_id)
	# 		post = [post] #so that if and else return the same type
	# 		#this should be served from memcache

	# 	else:
	# 		post = Wiki.load_topic(wiki_kw)[:1]

	# 	return post

	# def get_text(self, wiki_kw):
	# 	post_id = self.request.get('post_id')

	# 	if post_id:
	# 		post_id = int(post_id)
	# 		post = [Wiki.get_by_id(post_id)]
	# 	else:
	# 		post = self.get_last_post(wiki_kw)

	# 	if post:
	# 		text = post[0].text
	# 		return text
