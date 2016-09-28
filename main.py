# -*- coding: utf-8 -*-
from flask import Flask, render_template, request
app = Flask(__name__)
# Note: We don't need to call run() since our application is embedded within
# the App Engine WSGI application server.
import json
import re
from google.appengine.api import urlfetch

app.config.from_pyfile('settings.cfg')
STEAM_API_KEY = app.config['STEAM_API_KEY']

def convertToSteam64(steamID32):
	return int(steamID32.split(':')[2]) * 2 + int(steamID32.split(':')[1]) + 76561197960265728

def getHours(steamID64):
	hours = {}
	url = 'http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key=' + STEAM_API_KEY + '&steamid=' + str(steamID64) + '&format=json'
	response = urlfetch.fetch(url)
	data = json.loads(response.content)
	data = data['response']
	if 'games' in data:
		data = data['games']
		for game in data:
			if game['appid'] == 730:
				hours['forever'] = timeformat(game['playtime_forever'])
				hours['fortwoweeks'] = timeformat(game['playtime_2weeks'])
				return hours
	else: 
		hours['forever'] = '-'
		hours['fortwoweeks'] = '-'
	return hours

def getProfile(steamID64):
	info = {}
	allInfo = []
	url = 'http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key=' + STEAM_API_KEY + '&steamids=' + steamID64 + '&format=json'
	response = urlfetch.fetch(url)
	data = json.loads(response.content)
	data = data['response']
	data = data['players']
	dictSize = len(data) - 1
	i = 0
	while i <= dictSize:
		myDict = data[i]
		info['name'] = myDict['personaname']
		info['url'] = myDict['profileurl']
		info['avatar'] = myDict['avatar']
		hours = getHours(myDict['steamid'])
		info['vacfriends'] = getBannedFriends(myDict['steamid'])
		info.update(hours)
		info.update()
		allInfo.append(dict(info))
		i = i + 1
	return allInfo

def getBannedFriends(steamID64):
	friendlist = []
	urlIDList = ''
	url = 'http://api.steampowered.com/ISteamUser/GetFriendList/v0001/?key=' + STEAM_API_KEY + '&steamid=' + str(steamID64) +' &relationship=friend'
	response = urlfetch.fetch(url)
	data = json.loads(response.content)
	if 'friendslist' in data:
		data = data['friendslist']
		data = data['friends']
		steamIDs = ''
		for friend in data:
			urlIDList = urlIDList + str(friend['steamid']) + ','
		url = 'http://api.steampowered.com/ISteamUser/GetPlayerBans/v1/?key=' + STEAM_API_KEY + '&steamids=' + urlIDList
		response = urlfetch.fetch(url)
		data = json.loads(response.content)
		data = data['players']
		VACounter = 0
		for player in data:
			if player['VACBanned'] == True:
				VACounter = VACounter + 1
		return VACounter
	else:
		return '-'

def timeformat(minutes):
	hours = minutes // 60
	minutes = minutes - hours * 60
	return "%d.%02d" % (hours, minutes)

@app.route('/')
def default():
    """Return a friendly HTTP greeting."""
    return render_template('index.html', result='nonresult')

@app.route('/info', methods=['POST', 'GET'])
def getinfo():
	i = 0
	status = request.form['status']
	regex = 'STEAM.(.+?) +?'
	urlIDList = ''
	steamIDs = re.findall(regex, status)
	steamIDs = set(steamIDs)
	if (len(steamIDs) > 0 and len(steamIDs) < 20):
		for ID in steamIDs:
			ID = convertToSteam64(ID)
			urlIDList = urlIDList + str(ID) + '+'
		info = getProfile(urlIDList[:-1])
		return render_template('index.html', result='result', info = info)
	else:
		return render_template('index.html', result='nonresult')

@app.errorhandler(404)
def page_not_found(e):
    """Return a custom 404 error."""
    return 'Sorry, Nothing at this URL.', 404


@app.errorhandler(500)
def application_error(e):
    """Return a custom 500 error."""
    return 'Sorry, unexpected error: {}'.format(e), 500
