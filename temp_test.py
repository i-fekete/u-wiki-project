import urllib

def check_profanity(text):
	connection = urllib.urlopen('http://www.wdyl.com/profanity?q='+text)
	if 'true' in connection.read():
		profane = True
	connection.close()
	return profane


print check_profanity('shot')