import quandl
import requests
import datetime
import schedule
import time
import json
from firebase import firebase

firebase = firebase.FirebaseApplication('https://guap-6f88c.firebaseio.com/')
parameters = {'api_key': 'owtDCkSy4nZ7G7J1dSEa', 'order':'desc', 'rows':4}
FIREBASE_SECRET = 'Z2UD52Yp7TYKzkDD8GC7G5PgAPSGGKsdbpPsc3sL'
stock_tickers = firebase.get('/bets', None, params = {'shallow':'true', 'auth':FIREBASE_SECRET})

class Stock():
	_ticker = "GUAP"
	_prev_close = 0.00
	_today_close = 0.00
	current_date = datetime.datetime.strftime(datetime.datetime.now()-datetime.timedelta(1),'%Y-%m-%d')

	def __init__ (self, ticker):
		self._ticker = ticker
		result = requests.get('https://www.quandl.com/api/v3/datasets/WIKI/'+ ticker , params = parameters).json()
		self._prev_close = (result['dataset']['data'][1][4])
		self._today_close = (result['dataset']['data'][0][4])

	def getDirection(self):
		if self._prev_close < self._today_close:
			return True
		else:
			return False

	def getTicker(self):
		return self._ticker

	def getBettors(self):
		bettors = []
		try:
			bettors = (firebase.get('/bets/' +self._ticker, self.current_date,params = {'auth':FIREBASE_SECRET})['bettors'])
		except(KeyError):
			pass
		except(TypeError):
			pass
		for b in bettors:
			print (b)
		return bettors
	   

	def getWinningPool(self):
		winningPool = 0
		losingPool = 0
		bettors = self.getBettors()
		if len(bettors) > 0 and bettors != None:
			for index, bettor in enumerate(bettors):
				if (((bettor['direction'] == 'up') and (self.getDirection() == True)) or ((bettor['direction'] == 'down') and (self.getDirection() == False))):
					winningPool += float(bettor['amount'])
					bettor['isWinner'] = True
					firebase.patch('/bets/'+self._ticker+'/'+self.current_date+'/bettors/'+str(index),
									data = {'isWinner': True}, params = {'auth':FIREBASE_SECRET})
				else:
					losingPool += float(bettor['amount'])
					bettor['isWinner'] = False
					firebase.patch('/bets/'+self._ticker+'/'+self.current_date+'/bettors/'+str(index),
					 				data = {'isWinner': False}, params = {'auth':FIREBASE_SECRET})
			print (losingPool, winningPool)
			if winningPool == 0:
				pass
			else:
				payoutRatio = losingPool/winningPool * 0.9
				print (payoutRatio)
				for bettor in bettors:
					if bettor['isWinner'] == True:
						amt = float(bettor['amount']) * (1 + payoutRatio)
						if (firebase.get('/users/'+bettor['user']+'/Pending Bets',"amt_won", params = {'auth':FIREBASE_SECRET}) != None):
							amt_won = (firebase.get('/users/'+bettor['user']+'/Pending Bets',"amt_won", params = {'auth':FIREBASE_SECRET}))
							firebase.put('/users/'+bettor['user'], data={'amt_won': amt_won+ amt}, name = 'Pending Bets',params = {'auth':FIREBASE_SECRET})
							print(bettor['user']+' is already a winner, amount won: '+ str(amt_won))
						else:
							firebase.put('/users/'+bettor['user'], data = {'amt_won':amt}, name = 'Pending Bets', params = {'auth':FIREBASE_SECRET})
							print(bettor['user']+'\'s first win of the day, amount won: '+ str(amt))
						balance = float(firebase.get('/users/'+bettor['user']+"/Wallet", "deposit" , params = {'auth':FIREBASE_SECRET}))
						deposit = balance + amt
						
						firebase.patch('/users/'+bettor['user']+"/Wallet",
									data={'deposit': str(deposit)},
									params = {'auth':FIREBASE_SECRET})
					else:
						print(bettor['user']+" lost on "+ self._ticker)
						pass
		else:
			pass
def getLeaderboard():
	leaderboard = []
	users = firebase.get('/users', None, params = {'auth':FIREBASE_SECRET})
	json.dumps(users)
	for key, value in users.items():
		try:
			leaderboard.append(dict({'user':str(key), 'amt_won': (value['Pending Bets']['amt_won'])}))
		except:
			pass
	leaderboard = sorted(leaderboard, key=lambda k: k['amt_won'], reverse = True)
	firebase.put('/leaderboard/', data = leaderboard, name = 'Leaderboard', params = {'auth': FIREBASE_SECRET})

def newDateNodes():
def init_day():
    date = datetime.datetime.strftime(datetime.datetime.now()+datetime.timedelta(1),'%Y-%m-%d')
    print(date)
    for t in tic:
        firebase.put('/bets/'+t+'/'+date, data=0, name = "num-bettors-up",params={'auth':FIREBASE_SECRET})
        firebase.put('/bets/'+t+'/'+date, data=0, name = "num-bettors-down",params={'auth':FIREBASE_SECRET})    
    return redirect(url_for('entry'))

def clearPendingBets(username):
	try:
		pendingBets = (firebase.delete('/users/'+username,'Pending Bets', params = {'auth':FIREBASE_SECRET}))
	except(TypeError):
		pass

def sort():
	if len(stock_tickers) > 0:
		for ticker in stock_tickers:
			print (ticker)
			current_stock = Stock(ticker)
			current_stock.getWinningPool()
	else:
		pass


schedule.every().day.at("16:00").do(newDateNodes)
schedule.every().day.at("16:16").do(sort)
schedule.every().day.at("16:30").do(getLeaderboard)


while True:
    schedule.run_pending()
    time.sleep(1)