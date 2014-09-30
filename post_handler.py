from handlers import *


class WikiHandler(Handler):
	
	def get(self, path):
		last_post = Wiki.get_by_path(path).get()

		if last_post:
			self.render('wiki.html', path = path, text = last_post.text, **self.header)
		else:
			self.redirect('/_edit%s' % (path))


class EditHandler(Handler):
	
	def get(self, path):

		if not self.user:
			self.redirect('/login')

		# elif path == '/' and not self.user.admin:
		# 	self.write('This page cannot be edited by visitors')

		else:
			last_post = Wiki.get_by_path(path).get()

			if last_post:
				self.render('edit.html', path = path, text = last_post.text, **self.header)
			else:
				self.render('edit.html', path = path, **self.header)


	def post(self, path):
		text = self.request.get('content')

		new_entry = Wiki(parent = Wiki.parent_key(path), text = text)
		new_entry.put()
		
		self.redirect(path)

#This approach did not work with input with html code
#		if not is_profane(text):
#			new_entry = Wiki(path = path, text = text)
#			new_entry.put()
#
#			self.redirect(path)
#
#		else:
#			profanity_error = 'You seem to have used an inappropriate word (checked with www.wdyl.com)'
#			self.render('edit.html', path = path[1:], edit = True, text = text,
#			profanity_error = profanity_error, **self.header)
#

class HistoryHandler(Handler):
	
	def get(self, path):
		pass
		# if path == '/' and (not self.user or not self.user.admin):
		# 	history = Wiki.load_topic(path)[:1] #history html expects to get a list
		# 	#this is to ensure that the '/' page history cannot be viewed by others than the admins
		# 	#users not signed in or not admins view only the last page
		# 	#this should be changed to display an error message without redirecting to a short history page

		# else:
		# 	history = Wiki.load_topic(path)

		# self.render('history.html', path = path[1:], history = history, **self.header)
		# #history is also used by base.html to determine if history or view links should be displayed in the header



			

class IndexHandler(Handler):
	def get(self):
		pass
		# index, reconstructed = init_index()

		# index.sort(key = lambda s: s.lower())

		# self.render('index.html', index = index, **self.header)


class DeleteHandler(Handler):
	def get(self, path):
		pass
		# post_id = self.request.get('post_id')
		# if post_id:
		# 	post_id = int(post_id)
		# 	post = Wiki.get_by_id(post_id)
		# 	post.delete()

		# Wiki.load_topic(path, True)

		# self.redirect('/_history%s' % (path))