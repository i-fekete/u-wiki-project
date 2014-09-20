from handlers import *

class EditHandler(Handler):
	
	def get(self, wiki_kw):

		if not self.user:
			self.redirect('/login')

		elif wiki_kw == '/' and not self.user.admin:
			self.write('This page cannot be edited by visitors')

		else:
			post_id = self.request.get('post_id')

			if post_id:
				post_id = int(post_id[1:])
				post = Wiki.get_by_id(post_id)

			else:
				post = Wiki.load_topic(wiki_kw).get()
				
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
			index = []
			for keyword in db.GqlQuery("SELECT DISTINCT wiki_kw FROM Wiki"):#.order('wiki_kw')
				index.append(keyword.wiki_kw)			
		else:
			if wiki_kw not in index:
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

		if wiki_kw == '/' and (not self.user or not self.user.admin):
			history = [Wiki.load_topic(wiki_kw)[0]] #history html expects to get a list
			#this is to ensure that the '/' page history cannot be viewed by others than the admins
			#users not signed in or not admins view only the last page
			#this should be changed to display an error message without redirecting to a short history page

		else:
			history = Wiki.load_topic(wiki_kw)

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
			post = Wiki.load_topic(wiki_kw).get()
		
		if post:
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
		if not index:
			index = []
			for keyword in db.GqlQuery("SELECT DISTINCT wiki_kw FROM Wiki"):#.order('wiki_kw')
				index.append(keyword.wiki_kw)
				#this is a copy from edit, should avoid replication, maybe use bisect.insort

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