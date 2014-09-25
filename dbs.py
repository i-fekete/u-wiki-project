from google.appengine.ext import db
from google.appengine.api import memcache

from utils import *

import logging

def init_index():
		key = 'index'
		index = memcache.get(key)
		if not index:
			logging.info('Index DB hit')
			index = []
			for keyword in db.GqlQuery("SELECT DISTINCT wiki_kw FROM Wiki"):#.order('wiki_kw')
				index.append(keyword.wiki_kw)			
			
			memcache.set(key, index)
			return index, True

		else:
			return index, False

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
		'''
		Returns the list of posts associated with a wiki keyword and
		updates memcache if necessary

		wiki_kw - string, wiki keyword to look up in db / memcache
		update - boolean, True is used to update memcache after changes

		'''

		key = wiki_kw
		posts = memcache.get(key)

		if posts == None or update:

			#For some reason that needs to be investigated further the memcache
			#failes the update and does not return the most recent changes in db
			#To handle this the validator is set to the len of the posts before the
			#update and later checked if the len changed. It should try to update
			#memcache as long as the len does not change. The db is set up so that
			#any db change would change the length.

			if update:
				validator = len(posts)
			else:
				validator = 0

			counter = 0 #to handle long loops and get info on iterations

			while True:
				counter += 1
				posts = cls.all()
				posts = posts.filter('wiki_kw =', wiki_kw)
				posts = posts.order('-date')
				
				posts = list(posts)
				
				if validator != len(posts): #if len changes the update can take place
					logging.info("Number of iterations: %s" % (counter))
					break
				elif posts == None: #this is to check if the wiki_kw exists at all
					index, reconstructed = init_index()
					if posts not in index:
						break
				elif counter > 20: #this is to stop an infinite loop
					logging.error("You've created an infinite loop, congratulations")
					break

			memcache.set(key, posts)

		return posts
		