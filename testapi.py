#R. Yankou
#Google AppEngine app that accesses NPR's API and store favourited articles in a database

#MainPage: select a subject to search the 10 most recent articles (SearchPage) or navigate to Favourites (FavPage)
#SearchPage: select an article from its title, date, and teaser to display the full article (StoryPage)
#StoryPage: click top button to favourite the article (AddFav) or just read the article, audio not included (must visit NPR's page)
#AddFav: still shows article after storing its info to database but also lists favourited articles at bottom of page
#FavPage: shows favourited articles by title, date, and teaser; select one to view the full article (FavStory)
#FavStory: shows favourited story, using database instead of API to populate the page


import cgi
import datetime
import urllib
import wsgiref.handlers

from urllib2 import urlopen
from json import load

from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

mainpage_form="""<h1>Choose a category:</h1><br>
<form action="/search"><input type="radio" name="q" value=1045>Movies<br>
<input type="radio" name="q" value=1007>Science<br>
<input type="radio" name="q" value=1032>Economy<br>
<input type="radio" name="q" value=1039>Music<br>
<input type="submit" value="Search"></form>
<br>
<form action="/favourites"><input type="submit" name="f" value="Favourites"></form>"""

#Entries have only one element, a string called 'content' that can be multiple lines
class Entry(db.Model):
	title = db.StringProperty(multiline=True)
	iden = db.StringProperty(multiline=True)
	date = db.StringProperty(multiline=True)
	teaser = db.StringProperty(multiline=True)
	byline = db.StringProperty(multiline=True)
	show = db.StringProperty(multiline=True)
	url = db.StringProperty(multiline=True)
	image = db.StringProperty(multiline=True)
	caption = db.StringProperty(multiline=True)
	producer = db.StringProperty(multiline=True)
	audio = db.StringProperty(multiline=True)
	parag = db.TextProperty()

#Show radio buttons for search categories and a link to favourites
class MainPage(webapp.RequestHandler):
	def get(self):
		self.response.out.write(mainpage_form)

#Show 10 search results of given category by title, author, and date
class SearchPage(webapp.RequestHandler):
	def get(self):
		#base url + the apiKey param
		url = 'http://api.npr.org/query?apiKey=' 
		key = '' #your NPR API key here
		url = url + key
		url += '&numResults=10&format=json&id='
		cat_num = self.request.get("q") #category number
		url = url + cat_num
		url += '&requiredAssets=text,image,audio'

		#open our url, load the JSON
		response = urlopen(url)
		json_obj = load(response)

		self.response.out.write('<form action="/display">')

		#show title, author, date, teaser
		for story in json_obj['list']['story']:
			self.response.out.write('<input type="radio" name="p" value=%s>' %story['id'])
			self.response.out.write('<b><em>Title: %s </em></b>&nbsp' %story['title']['$text'])
			self.response.out.write('Date: %s <br>' %story['storyDate']['$text'])
			self.response.out.write('Teaser: %s <br>' %story['teaser']['$text'])
			self.response.out.write('<br>')

		self.response.out.write('<input type="submit" value="Search"></form>')
		self.response.out.write('<form action="/"><input type="submit" name="h" value="Go Home"></form>')		

#Show selected story
class StoryPage(webapp.RequestHandler):
	def get(self):
		#base url + the apiKey param
		url = 'http://api.npr.org/query?apiKey=' 
		key = '' #your NPR API key here
		url = url + key
		url += '&numResults=1&format=json&id='
		cat_num = self.request.get("p") #category number
		url = url + cat_num
		url += '&requiredAssets=text,image,audio'

		#open our url, load the JSON
		response = urlopen(url)
		json_obj = load(response)

		#show title, author, date, teaser
		for story in json_obj['list']['story']:
			#include favourite button
			self.response.out.write('<form action="/addfav"><input type="submit" name="fa" value="%s">Click to Fav</form>' %story['id'])

			self.response.out.write('<b><em> %s </em></b>&nbsp' %story['title']['$text'])
			self.response.out.write(' %s <br><br>' %story['storyDate']['$text'])
			self.response.out.write(' %s <br><br>' %story['teaser']['$text'])

			if 'byline' in story:
				self.response.out.write('BYLINE: %s <br>' %story['byline'][0]['name']['$text'] )
	
			if 'show' in story:
				self.response.out.write('PROGRAM: %s <br>' %story['show'][0]['program']['$text'] )
	
			self.response.out.write('<a href="%s">NPR URL</a> <br>' %story['link'][0]['$text'])

			self.response.out.write('<img src="%s" alt="Story Image"> <br>' %story['image'][0]['src'])

			if 'caption' in story:
				self.response.out.write('IMAGE CAPTION: %s <br>' %story['image'][0]['caption']['$text'] )
	
			if 'producer' in story:
				self.response.out.write('IMAGE CREDIT: %s <br>' %story['image'][0]['producer']['$text'] )

			#self.response.out.write('<audio controls><source src="%s" type="audio/mpeg">Your browser does not support the audio element.</audio> <br>' %story['audio'][0]['format']['mp3'][0]['$text'])
	
			self.response.out.write('MP3 AUDIO: %s <br><br>' %story['audio'][0]['format']['mp3'][0]['$text'] )	
	
			#loop through and print each paragraph
			self.response.out.write('<p>')
			for paragraph in story['textWithHtml']['paragraph']:
				self.response.out.write(paragraph['$text'] + '<br>')
			self.response.out.write('</p>')

		self.response.out.write('<form action="/"><input type="submit" name="h" value="Go Home"></form>')			

#Store favourited article to database
class AddFav(webapp.RequestHandler):
	def get(self):
		#Get the favourited story's id
		Iden = self.request.get("fa")

		entry=Entry()
		entry.iden = Iden

		#base url + the apiKey param
		url = 'http://api.npr.org/query?apiKey=' 
		key = '' #your NPR API key here
		url = url + key
		url += '&numResults=1&format=json&id='
		url = url + Iden
		url += '&requiredAssets=text,image,audio'

		#open our url, load the JSON
		response = urlopen(url)
		json_obj = load(response)

		#show title, author, date, teaser
		for story in json_obj['list']['story']:

			entry.title = story['title']['$text']
			entry.date = story['storyDate']['$text']
			entry.teaser = story['teaser']['$text']

			if 'byline' in story:
				entry.byline = story['byline'][0]['name']['$text']
	
			if 'show' in story:
				entry.show = story['show'][0]['program']['$text']

			entry.url = story['link'][0]['$text']

			entry.image = story['image'][0]['src']

			if 'caption' in story:
				entry.caption = story['image'][0]['caption']['$text']
	
			if 'producer' in story:
				entry.producer = story['image'][0]['producer']['$text']

			entry.audio = story['audio'][0]['format']['mp3'][0]['$text']
	
			#loop through and print each paragraph
			entry.parag = '<p>'
			for paragraph in story['textWithHtml']['paragraph']:
				entry.parag = entry.parag + '</p>' +paragraph['$text']
			entry.parag = entry.parag + '</p>'

			entry.put()

			#Now display the page again
			self.response.out.write('<b><em> %s </em></b>&nbsp' %story['title']['$text'])
			self.response.out.write(' %s <br><br>' %story['storyDate']['$text'])
			self.response.out.write(' %s <br><br>' %story['teaser']['$text'])

			if 'byline' in story:
				self.response.out.write('BYLINE: %s <br>' %story['byline'][0]['name']['$text'] )
	
			if 'show' in story:
				self.response.out.write('PROGRAM: %s <br>' %story['show'][0]['program']['$text'] )
	
			self.response.out.write('<a href="%s">NPR URL</a> <br>' %story['link'][0]['$text'])

			self.response.out.write('<img src="%s" alt="Story Image"> <br>' %story['image'][0]['src'])

			if 'caption' in story:
				self.response.out.write('IMAGE CAPTION: %s <br>' %story['image'][0]['caption']['$text'] )
	
			if 'producer' in story:
				self.response.out.write('IMAGE CREDIT: %s <br>' %story['image'][0]['producer']['$text'] )

			#self.response.out.write('<audio controls><source src="%s" type="audio/mpeg">Your browser does not support the audio element.</audio> <br>' %story['audio'][0]['format']['mp3'][0]['$text'])
	
			self.response.out.write('MP3 AUDIO: %s <br><br>' %story['audio'][0]['format']['mp3'][0]['$text'] )	
	
			#loop through and print each paragraph
			self.response.out.write('<p>')
			for paragraph in story['textWithHtml']['paragraph']:
				self.response.out.write(paragraph['$text'] + '<br>')
			self.response.out.write('</p>')
			
			#show the currently fav'd titles
			self.response.out.write('Favourites: <br>')
			entries=db.GqlQuery("SELECT * FROM Entry")
			for entry in entries:
				self.response.out.write('<b><em>Title: %s </em></b><br>' %entry.title)

			self.response.out.write('<form action="/"><input type="submit" name="h" value="Go Home"></form>')			


#Show titles to favourites with select links
class FavPage(webapp.RequestHandler):
	def get(self):
		#Read titles from database
		entries=db.GqlQuery("SELECT * FROM Entry")

		self.response.out.write('<form action="/dispfav">')

		#show title, author, date, teaser
		for entry in entries:
			self.response.out.write('<input type="radio" name="p" value=%s>' %entry.iden)
			self.response.out.write('<b><em>Title: %s </em></b>&nbsp' %entry.title)
			self.response.out.write('Date: %s <br>' %entry.date)
			self.response.out.write('Teaser: %s <br>' %entry.teaser)
			#self.response.out.write('<input type="radio" name="p" value=%s>' %cgi.escape(entry.iden))
			#self.response.out.write('<b><em>Title: %s </em></b>&nbsp' %cgi.escape(entry.title))
			#self.response.out.write('Date: %s <br>' %cgi.escape(entry.date))
			#self.response.out.write('Teaser: %s <br>' %cgi.escape(entry.teaser))
			self.response.out.write('<br>')

		self.response.out.write('<input type="submit" value="Search"></form>')
		self.response.out.write('<form action="/"><input type="submit" name="h" value="Go Home"></form>')

#Show favourited story from database (no API needed/used)
class FavStory(webapp.RequestHandler):
	def get(self):
		#Read titles from database
		iden = self.request.get("p")
		entries=db.GqlQuery("SELECT * FROM Entry WHERE iden = :1", iden)

		#show title, author, date, teaser
		for entry in entries:
			self.response.out.write('<b><em> %s </em></b>&nbsp' %entry.title)
			self.response.out.write(' %s <br><br>' %entry.date)
			self.response.out.write(' %s <br><br>' %entry.teaser)

			if entry.byline:
				self.response.out.write('BYLINE: %s <br>' %entry.byline )
	
			if entry.show:
				self.response.out.write('PROGRAM: %s <br>' %entry.show )
	
			self.response.out.write('<a href="%s">NPR URL</a> <br>' %entry.url)

			self.response.out.write('<img src="%s" alt="Story Image"> <br>' %entry.image)

			if entry.caption:
				self.response.out.write('IMAGE CAPTION: %s <br>' %entry.caption)
	
			if entry.producer:
				self.response.out.write('IMAGE CREDIT: %s <br>' %entry.producer)

			#self.response.out.write('<audio controls><source src="%s" type="audio/mpeg">Your browser does not support the audio element.</audio> <br>' %story['audio'][0]['format']['mp3'][0]['$text'])
	
			self.response.out.write('MP3 AUDIO: %s <br><br>' %entry.audio )	
	
			#loop through and print each paragraph
			self.response.out.write('%s' %entry.parag)

		self.response.out.write('<form action="/"><input type="submit" name="h" value="Go Home"></form>')

#Update to include all url's and their RequestHandler classes
application = webapp.WSGIApplication(
                                     [('/', MainPage),
					     ('/search',SearchPage),
					     ('/display',StoryPage),
					     ('/addfav',AddFav),
					     ('/favourites',FavPage),
					     ('/dispfav',FavStory)],
                                     debug=True)

#Run the app
def main():
    run_wsgi_app(application)

#not sure what this does
if __name__ == "__main__":
    main()

