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
		user.filter('name =', name)
		user.get()
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
	text = db.TextProperty(required = True)
	date = db.DateTimeProperty(auto_now_add = True)

	@staticmethod
	def parent_key(path):
		return db.Key.from_path('/root' + path, 'posts')

	@classmethod
	def get_by_path(cls, path):
		posts = cls.all()
		posts.ancestor(cls.parent_key(path))
		posts.order('-date')

		return posts
		