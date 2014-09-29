from utils import *

import logging, \
	urllib, \
	webapp2

from handlers import *
from user_handler import *
from post_handler import *
from dbs import *

#for making secure cookies


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



PAGE_RE = r'(/(?:[a-zA-Z0-9_-]+/?)*)'
app = webapp2.WSGIApplication([
	('/login', LoginHandler),
	('/signup', SignupHandler),
	('/logout', LogoutHandler),
	('/index', IndexHandler),
	('/users', UserHandler),
	('/_edit' + PAGE_RE, EditHandler),
	('/_history' + PAGE_RE, HistoryHandler),
	('/_del' + PAGE_RE, DeleteHandler),
	(PAGE_RE, WikiHandler),
	], debug=True)