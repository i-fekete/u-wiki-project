from handlers import *

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
			users = User.all()
			if users.count(1): #if User is empty, the first user will be set to admin
				self.admin = False
			else:
				self.admin = True
			new_user = User.register(self.username, self.password, self.admin, self.email)
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


class UserHandler(Handler):

	def get(self):

		if not self.user:
			self.redirect('/login')

		elif not self.user.admin:
			self.write('You need to be an admin to visit this page')

		else:
			users = User.all()
			users = list(users)

			self.render('users.html', users = users, **self.header)