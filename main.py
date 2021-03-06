import requests
import time
import trip_advisor_api as TripAPI
import enchant
import os

ACCESS_TOKEN = os.environ['GROUPME_TOKEN']
group_id = os.environ['GROUPME_GROUP_ID']
bot_name = "Foo-Bot"
bot_id = os.environ['GROUPME_BOT_ID']
keyword = "@foo-bot" #keyword to summon the bot
name = "" #this will be modified by main() -- do not touch
d = enchant.Dict('en_US')

def main():
	nameMessages = getMessagesName()
	messages = getMessages()
	found, message = hasCallWord(messages)
	if found:
		global name
		name = nameMessages
		apathy = requestApathy() #of the form (user_id, apathy level)
		if len(apathy) == 0:
			while len(apathy) == 0:
				sendMessage("Whoops, looks like there isn't enough information for me to really do much... why don't you try again?")
				apathy = requestApathy()
		cuisine = requestCuisine()
		if len(cuisine) == 0:
			while len(cuisine) == 0:
				sendMessage("Whoops, looks like there isn't enough information for me to really do much... why don't you try again?")
				cuisine = requestCuisine()
		cuisine = cuisineDict(apathy, cuisine)
		price = requestPrice()
		if price == 0:
			while price == 0:
				sendMessage("Whoops, looks like there isn't enough information for me to really do much... why don't you try again?")
				price = requestPrice()
		zips = requestZips()
		if len(zips) == 0:
			 while zips == 0:
				sendMessage("Whoops, looks like there isn't enough information for me to really do much... why don't you try again?")
				zips = requestZips()
		location_json = TripAPI.getRestaurantJson(cuisine, price, zips)
		results = []
		if location_json['paging']['results'] > 0:
			for location in location_json['data'][-3:]:
				results.append({
					'name': location['name'],
					'street': location['address_obj']['street1'],
					'city': location['address_obj']['city'],
					'avg_distance': location['distance'],
					'web_url': location['web_url'],
					'price_level': location['price_level'],
					'cuisine': location['cuisine']
				})
			sendMessage("Here's what I found!")
		for result in results:
			sendMessage(result['name'] + "\n" + result['street'] + ", " + result["city"] + "\n" + result['web_url'])
			time.sleep(1)
	return 0

def getMessages():
	'''
	returns messages in the form [(user_id, message),...] since last bot posting.
	'''
	messages = []
	r = requests.get("https://api.groupme.com/v3/groups/{}/messages?token={}".format(group_id, ACCESS_TOKEN))
	for message in r.json()["response"]["messages"]:
		# print r.json()
		if message['name'] == bot_name:
			break
		# print message['text']
		messages += [[message['sender_id'], message['text']]]
	return messages

def getMessagesName():
	'''
	returns messages in the form [[sender_id, name, text],...] since last bot posting.
	'''
	messages = []
	r = requests.get("https://api.groupme.com/v3/groups/{}/messages?token={}".format(group_id, ACCESS_TOKEN))
	for message in r.json()["response"]["messages"]:
		# print r.json()
		if keyword.upper() in message['text'].upper():
			return message['name']
	return ""

def hasCallWord(messages):
	for message in messages:
		if keyword.upper() in message[1].upper():
			return True, message
	return False, []

def hasDone(messages):
	return "DONE" in map(lambda x:x[1].upper().strip(),messages)

def sendMessage(message):
	r = requests.post("https://api.groupme.com/v3/bots/post", data={"bot_id": bot_id, "text": message})
	# print "\"" + message + "\" posted\n"
def sendPictureMessage(message, image_url):
	r = requests.post("https://api.groupme.com/v3/bots/post", data={"bot_id": bot_id, "text": message, "picture_url": image_url})
	# print "\"" + message + "\" posted with picture\n"
def requestApathy():
	'''
	returns array with [[user_id, apathy level],...] as struct
	'''
	sendMessage("(1/4) how picky are you? Reply with a number (1-10, 1 being indifferent and 10 being extremely picky). " + str(name) + " type \"done\" when everyone is finished!")
	found = False
	while not found:
		messages = getMessages()
		if hasDone(messages):
			found = True
		time.sleep(1)
	messages = filterForInt(messages)
	return messages

def filterForInt(messages):
	'''
	[[user_id, message]] -> [[user_id, int(message)]]
	removes any invalid messages
	'''
	toRemove = []
	for message in messages:
		try:
			if int(message[1]) <= 10 and int(message[1]) >= 1:
				message[1] = int(message[1])
			else:
				toRemove += [message]
		except ValueError, e:
			# print "One user has entered an invalid entry:", e, message[1]
			toRemove += [message]
	for message in toRemove:
		messages.remove(message)
	return messages

def requestCuisine():
	'''
	-> [(0,0)]
	returns array with [(user_id, food_type),...] as struct
	foods list from TripAdvisor API
	'''
	foods = ['African', 'American', 'Asian', 'Bakery', 'Barbecue', 'British', 'Cafe', 'Cajun & Creole', 'Caribbean', 'Chinese', 'Continental', 'Delicatessen', 'Dessert', 'Eastern European', 'Fusion / Eclectic', 'European', 'French', 'German', 'Global / International', 'Greek', 'Indian', 'Irish', 'Italian', 'Japanese', 'Mediterranean', 'Mexican / Southwestern', 'Middle Eastern', 'Pizza', 'Pub', 'Seafood', 'Soups', 'South American', 'Spanish', 'Steakhouse', 'Sushi', 'Thai', 'Vietnamese']
	sendMessage("(2/4) what are you in the mood for? Type your favorite style of food. " + str(name) + ", type \"done\" when everyone is finished!")
	found = False
	while not found:
		messages = getMessages()
		if hasDone(messages):
			found = True
		time.sleep(1)
	toRemove = []
	for message in messages:
		found = False
		for food in foods:
			if message[1].encode('UTF-8').strip() in food.upper(): #enables user to type Deli instead of delicatessen
				message[1] = food
				found = True
				break
			elif "BURGER" in message[1].upper(): #Handling limited edge case
				message[1] = 'American'
				found = True
				break
			elif not d.check(message[1].lower().title()):
				for suggestion in d.suggest(message[1].lower().title()) + ["burger"]:
					if food.lower() == suggestion.lower():
						sendMessage("Interpreting {} as {}".format(message[1], food))
						message[1] = food
						found = True
						break

		if not found:
			messages.remove(message)
	return messages

def cuisineDict(apathy, food):
	'''
	[[user_id, apathy],...], [[user_id, food],...] -> dict(food:weighted_count)
	'''
	cuisine = {}
	for aitem in apathy:
		for fitem in food[:-1]:
			# print fitem
			if aitem[0] == fitem[0]:
				cuisine[fitem[1]] += int(aitem[1])
	# print cuisine
	return cuisine

def requestPrice():
	'''
	-> int
	returns average price
	'''
	sendMessage("(3/4) how much are you looking to spend? On a scale of 1-4, type your price level (1 being cheapest and 4 being most expensive). " + str(name) + ", type \"done\" when everyone is finished!")
	found = False
	total = 0 #total of prices for averaging
	seen = [] #to prevent duplicate prices being posted, only last entry counts
	text = []
	while not found:
		messages = getMessages()
		if hasDone(messages):
			found = True
		time.sleep(1)
	messages = messages[1:]
	toRemove = []
	for message in messages:
		try:
			if message[0] not in seen and int(message[1]) >= 1 and int(message[1]) <= 4:
				seen += [message[0]]
				text += [message[1]]
		except ValueError, e:
			# print "One user has entered an invalid entry:", e, message[1]
			toRemove += [message]
	for message in toRemove:
		messages.remove(message)
	for message in text:
		total += int(message) #sum all price values
	if len(text) == 0:
		return 0
	return int(total/len(text)) #take average with round-down (inability to spend money takes priority)

def requestZips():
	'''
	-> [str]
	returns list with [zip_code,...]
	'''
	sendMessage("(4/4) Please reply with the relevant zip code(s). " + str(name) + ", type \"done\" when everyone is finished!")
	found = False
	zips = []
	while not found:
		messages = getMessages()
		if hasDone(messages):
			found = True
		time.sleep(1)
	toRemove = []
	for message in messages[1:]:
		if not message[1].isdigit() and len(message[1]) == 5:
			toRemove += [message]
		else:
			zips += [message[1]]
	for message in toRemove:
		messages.remove(message)
	# print zips
	return zips

if __name__ == '__main__':
	main()
