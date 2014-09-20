from google.appengine.ext import db
from google.appengine.api import memcache

from utils import *

import logging

class User(db.Model):
	name = db.StringProperty(required = True)
	pw_hash = db.StringProperty(required = True)
	email = db.StringProperty()
	admin = db.BooleanProperty(default = False)

	@classmethod
	def by_id(cls, uid):
		return cls.get_by_id(uid)

	@classmethod
	def by_name(cls, name):
		user = cls.all()
		user = user.filter('name =', name)
		user = user.get()
		return user

	@classmethod
	def register(cls, name, password, admin, email = None):
		pw_hash = make_pw_hash(name, password)
		return cls(name = name, pw_hash = pw_hash, email = email, admin = admin)

	@classmethod
	def login(cls, name, password):
		user = cls.by_name(name)
		if user and valid_login(name, password, user.pw_hash):
			return user


class Wiki(db.Model):
	wiki_kw = db.StringProperty(required = True)
	text = db.TextProperty(required = True)
	date = db.DateTimeProperty(auto_now_add = True)

	@classmethod
	def load_topic(cls, wiki_kw, update = False):
		return cls.all().filter('wiki_kw =', wiki_kw).order('-date')

		# key = wiki_kw
		# posts = memcache.get(key)
		
		# if posts == None or update:
		# 	logging.info('DB hit')
		# 	posts = cls.all()
		# 	posts = posts.filter('wiki_kw =', wiki_kw)
		# 	posts = posts.order('-date')
			
		# 	posts = list(posts)
		# 	memcache.set(key, posts)

		# return posts
		