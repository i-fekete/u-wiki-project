from handlers import *

class EditHandler(Handler):
	
	def get(self, wiki_kw):

		if not self.user:
			self.redirect('/login')

		elif wiki_kw == '/' and not self.user.admin:
			self.write('This page cannot be edited by visitors')

		else:
			post = self.get_last_post(wiki_kw)

			if post:
				text = post[0].text
				self.render('edit.html', wiki_kw = wiki_kw[1:], edit = True, text = text, **self.header)
				#edit is passed in for the base.html to check which links to display in the header
			else:
				self.render('edit.html', wiki_kw = wiki_kw[1:], **self.header)


	def post(self, wiki_kw):
		
		text = self.request.get('content')

		new_entry = Wiki(wiki_kw = wiki_kw, text = text)
		if new_entry.put():

			#updating index memcache if a new keyword has been added
			index, reconstructed = init_index()
			if not reconstructed:
			#if a new index has been created there is no need to update
				if wiki_kw not in index:
					index.append(wiki_kw)
					memcache.set('index', index)


			#updating keyword memcache with every post
			Wiki.load_topic(wiki_kw, True)

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
			history = Wiki.load_topic(wiki_kw)[:1] #history html expects to get a list
			#this is to ensure that the '/' page history cannot be viewed by others than the admins
			#users not signed in or not admins view only the last page
			#this should be changed to display an error message without redirecting to a short history page

		else:
			history = Wiki.load_topic(wiki_kw)

		self.render('history.html', wiki_kw = wiki_kw[1:], history = history, **self.header)
		#history is also used by base.html to determine if history or view links should be displayed in the header


class WikiHandler(Handler):
	
	def get(self, wiki_kw):
		post = self.get_last_post(wiki_kw)
		
		if post:
			text = post[0].text#.replace('\n', '<br>')
			#uncomment above to allow proper line brakes in non-html posts
			self.render('wiki.html', wiki_kw = wiki_kw[1:], text = text, **self.header)
		else:
			self.redirect('/_edit%s' % (wiki_kw))
			

class IndexHandler(Handler):
	def get(self):
		index, reconstructed = init_index()

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

class DeleteHandler(Handler):
	def get(self, wiki_kw):
		post_id = int(self.request.get('post_id')[1:])
		post = Wiki.get_by_id(post_id)
		post.delete()

		Wiki.load_topic(wiki_kw, True)

		self.redirect('/_history%s' % (wiki_kw))