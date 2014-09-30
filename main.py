from utils import *

import logging, \
	urllib, \
	webapp2

from handlers import *
from user_handler import *
from post_handler import *
from dbs import *


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