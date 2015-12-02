#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pushbullet import Pushbullet
import logging
import requests
import sqlite3
import json
import time
import sys
import os
import gc

DEBUG = True
PATH = os.path.dirname(os.path.abspath(__file__))

class GameChanger(object):
	"""Check for a game change of a twitch streamer"""
	def __init__(self):
		logging.basicConfig(filename=os.path.join(PATH, 'log.txt'), level=logging.DEBUG,
							format='%(asctime)s - %(levelname)s - %(message)s')
		api_key, client_id, oauth, streamers = self.get_config()
		self.init_db()
		self.pbullet = Pushbullet(api_key)
		if DEBUG:
			self.pbullet.push_note("Test", "This is a debug message.")
		for streamer in streamers:
			### Url to Twitch API (see https://github.com/justintv/Twitch-API) ###
			url = "https://api.twitch.tv/kraken/streams/{0}".format(streamer)
			self.check_stream(streamer, client_id, url, oauth)

	### Get the config data from "config.cfg" file in same folder ###
	def get_config(self):
		"""Get config settings from config.cfg"""
		if os.path.isfile(os.path.join(PATH, "config.cfg")):
			config_data = json.load(open(os.path.join(PATH, "config.cfg")))
			api_key = config_data["api_key"]
			client_id = config_data["client_id"]
			oauth = config_data["oauth"]
			streamers = config_data["streamers"]
			return api_key, client_id, oauth, streamers
		else:
			cfg = {
				"api_key":"",
				"client_id": "",
				"oauth": "",
				"streamers": []
			}
			json.dump(cfg, open(os.path.join(PATH, "config.cfg"), "w"))
			logging.warning("Please update the config.cfg!")
			sys.exit()

	### Initialize the database if not yet initiated ###
	def init_db(self):
		"""Initialize the database if not already done"""
		if not os.path.isfile(os.path.join(PATH, "games.db")):
			logging.debug("Initiating database.")
			conn = sqlite3.connect(os.path.join(PATH, "games.db"))
			cursor = conn.cursor()
			cursor.execute("""CREATE TABLE games (streamer TEXT PRIMARY KEY,
					  game TEXT, last_changed TEXT)""")
			conn.commit()
			conn.close()
			gc.collect()
		else:
			return

	### Check the database for the streamer and game ###
	def check_db(self, streamer, game):
		"""Check the database entry for a given streamer"""
		conn = sqlite3.connect(os.path.join(PATH, "games.db"))
		cursor = conn.cursor()
		cursor.execute("""SELECT * FROM games WHERE streamer=?""", (streamer,))
		result = cursor.fetchone() #returns as a tuple e.g.(u'lirik', u'Arma3', u'2015-12-02 18:30')
		if result == None:
			cursor.execute("""INSERT INTO games VALUES (?,?,?)""", [streamer, game,
												time.strftime("%Y-%m-%d %H:%M", time.localtime())])
		else:
			if game != result[1]:
				cursor.execute("""UPDATE games SET game=?, last_changed=? WHERE streamer=?""",
				  [game, time.strftime("%Y-%m-%d %H:%M", time.localtime()), streamer])
				self.send_notification(streamer, game)
		conn.close()
		gc.collect()

	### Send a pushbullet notification with streamer and game ###
	def send_notification(self, streamer, game):
		"""Send a pushbullet notification to the user"""
		logging.debug("Sending notification.")
		self.pbullet.push_note("Twitch Notify", "{0} is now playing {1}.".format(streamer, game))

	### Access Twitch Api to check if the game has changed ###
	def check_stream(self, streamer, client_id, url, oauth):
		"""Access the TwitchAPI to get information about a stream/streamer"""
		headers = {
			"Accept": "application/vnd.twitchtv.v3+json",
			"client_id": client_id,
			"Authorization": "OAuth {0}".format(oauth)
		}
		### Request json about the streamer ###
		data = requests.get(url, headers=headers)
		### Check the responses status code and act accordingly ###
		if data.status_code != 200:
			json.dump(data.json(), open(os.path.join(PATH, "bad_response.json"), "w"))
			logging.warning("Bad response code: {0}\nCheck bad_response.json".format(data.status_code))
			sys.exit()
		else:
			data = data.json()
		### Parse the json from the response ###
		if data["stream"] != None:
			now_playing = data["stream"]["game"]
			self.check_db(streamer, now_playing)


if __name__ == "__main__":
	TIME1 = time.time()
	GameChanger()
	TIME2 = time.time()
	logging.debug("The script took %.2f seconds.", (TIME2 - TIME1))
