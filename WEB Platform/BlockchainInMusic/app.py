import pyrebase
from flask import *
import datetime
from flask import jsonify, request
from datetime import date
from werkzeug.utils import secure_filename
import unicodedata
from hashlib import sha256
import json
import threading
from time import sleep
import requests
import random

from flask_table import Table, Col

config = {
	"apiKey": "AIzaSyBqJmj4LU6gnEVdX-KUsj6IqTR3Rq0kygs",
	"authDomain": "blockchain-in-music.firebaseapp.com",
	"databaseURL": "https://blockchain-in-music.firebaseio.com",
	"projectId": "blockchain-in-music",
	"storageBucket": "blockchain-in-music.appspot.com",
	"messagingSenderId": "559996951702",
	"appId": "1:559996951702:web:12d3b2716399ecc943f6b7",
	"measurementId": "G-18NBTS9NPH"

}

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif', 'mp3', 'wav', 'flac'])

firebase = pyrebase.initialize_app(config)

auth = firebase.auth()
db = firebase.database()
storage = firebase.storage()

#############################################################################################

nodes_set = set()  # A set to save list of nodes in the distributed network
Pending_Transactions = []  # A list to store pending transactions
semaphore = {}  # dictionary for blockchain critical section


def generate_block():
	if len(Pending_Transactions) > 1:
		temp = ""
		for t in Pending_Transactions:
			temp += t

		transaction_id = sha256(temp.encode()).hexdigest()
		for node in nodes_set:
			url = node + "mine"
			data = {"transaction": Pending_Transactions,
			        "transaction_id": transaction_id
			        }
			headers = {'Content-Type': "application/json"}
			response = requests.post(url, data=json.dumps(data), headers=headers)

		Pending_Transactions.clear()


# class myThread(threading.Thread):
# 	def __init__(self, threadID, name):
# 		threading.Thread.__init__(self)
# 		self.threadID = threadID
# 		self.name = name
#
# 	def run(self):
# 		while True:
# 			generate_block()
# 			sleep(5)
#
#
# # Create new threads
# thread1 = myThread(1, "Generate Blocks")
#
# # Start new Threads
# thread1.start()
# thread1.join()


# if response.status_code == 200:
# 	length = response.json()['length']
# 	self.nodes_set.update(response.json()['nodes'])
# 	return True
# else:
# 	return False


def add_transaction(trans_str):
	transaction_hash = sha256(trans_str.encode()).hexdigest()
	Pending_Transactions.append(transaction_hash)


##############################################################################


def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def unicode_to_string(uni):
	return unicodedata.normalize('NFKD', uni).encode('ascii', 'ignore')


# def noquote(s):
#    return s
# pyrebase.pyrebase.quote = noquote

# db.child("distributor").push({"company_name":"spotify"})
# db.child("distributor").child("name").update({"company_name":"Spotify"})

# distributors = db.child("distributor").child("name").get()
# print(distributors.val())
# print(distributors.key())

# db.child("distributor").child("name").remove()

app = Flask(__name__)
app.secret_key = "super secret key"


# @app.after_request
# def after_request(response):
#    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
#    return response


@app.route('/', methods=['GET', 'POST'])
def home():
	if request.method == 'POST':
		email = request.form['email']
		passwd = request.form['pass']
		try:
			user = auth.sign_in_with_email_and_password(email, passwd)
			localId = user['localId']
			session['localId'] = localId
		except:
			flash('Email or Password Incorrect!', 'error')
			return redirect(url_for('home'))

		dis = db.child('distributors').get()
		pro = db.child('producers').get()

		if dis.val() != None:
			if localId in dis.val().keys():
				return redirect(url_for('dis_home'))

		if pro.val() != None:

			if localId in pro.val().keys():
				return redirect(url_for('pro_home'))

	session['localId'] = None
	return render_template("login.html")


@app.route('/dis_sign_up', methods=['GET', 'POST'])
def dis_sign_up():
	if request.method == 'POST':
		name = request.form['name']
		gender = request.form['gender']
		email = request.form['email']
		password = request.form["pass"]
		phone_no = request.form['phone']
		company_name = request.form['company_name']
		app_name = request.form['app_name']
		api_key = str(
			name + str(phone_no[:len(phone_no) // 2]) + app_name + str(phone_no[len(phone_no) // 2:]) + email.replace(
				'.', ''))

		search_ph = db.child("distributors").get()
		if search_ph.val() != None:
			for i in search_ph.val().values():
				if phone_no in i.values():
					flash('Phone Number already exists!', 'error')

					return redirect(url_for('dis_sign_up'))

		try:
			user = auth.create_user_with_email_and_password(email, password)
			db.child("distributors").child(user['localId']).set(
				{"name": name, "gender": gender, "email": email, "api_key": api_key, "company_name": company_name,
				 "app_name": app_name, 'phone': phone_no, "contracts": 0, "active_contracts": 0, "views": 0,
				 "revenue": 0})
		except:
			flash('Email already Exists!', 'error')

			return redirect(url_for('dis_sign_up'))

		flash('Successfully Registered! Login to Continue ... ', 'info')
		return redirect(url_for('home'))

	return render_template("dis_sign_up.html")


@app.route('/pro_sign_up', methods=['GET', 'POST'])
def pro_sign_up():
	if request.method == 'POST':
		name = request.form["name"]
		bday = request.form["bday"]
		age = int(date.today().year) - int(bday[4:])
		gender = request.form["gender"]
		email = request.form["email"]
		phone_no = str(request.form["phone"])
		company_name = request.form["company_name"]
		password = request.form["pass"]
		api_key = str(name + str(phone_no[:len(phone_no) / 2]) + str(company_name) + str(
			phone_no[len(phone_no) / 2:]) + email.replace('.', ''))

		search_phone = db.child("producers").get()
		if search_phone.val() != None:
			for i in search_phone.val().values():
				if phone_no in i.values():
					flash('Phone Number already exists!', 'error')

					return redirect(url_for('pro_sign_up'))

		try:
			user = auth.create_user_with_email_and_password(email, password)
			db.child("producers").child(user['localId']).set(
				{"name": name, "bday": bday, "age": age, "gender": gender, "email": email, "company_name": company_name,
				 "api_key": api_key, "phone": phone_no, "contracts": 0, "active_contracts": 0, "views": 0,
				 "revenue": 0})
		except:
			flash('Email already Exists!', 'error')

			return redirect(url_for('pro_sign_up'))

		flash('Successfully Registered! Login to Continue ... ', 'info')
		return redirect(url_for('home'))

	return render_template("pro_sign_up.html")


@app.route('/pro_home', methods=['GET', 'POST'])
def pro_home():
	localId = session["localId"]
	name = db.child('producers').child(localId).child('name').get()
	contract = db.child('producers').child(localId).child('contracts').get()
	ac_contract = db.child('producers').child(localId).child('active_contracts').get()
	view = db.child('producers').child(localId).child('views').get()
	rev = db.child('producers').child(localId).child('revenue').get()

	# for album loading
	albums = []
	album_arts = []
	if db.child('albums').child(localId).get().val().values():
		for i in db.child('albums').child(localId).get().val().values():
			albums.append(i['album_name'])
		for j in albums:
			album_arts.append(str(storage.child(localId).child('album_arts').child(j).get_url(1)))

	# for contract loading

	pending_contracts = []
	active_contracts = []
	if db.child('contracts').get().val().values():
		for i in db.child('contracts').get().val().values():
			if i['pro_id'] == localId:
				if i['status'] == 'pending':
					pending_contracts.append({"Contract Name ": i['c_name'], "Album Name ":
						list(db.child('albums').child(localId).child(i['alb_id']).get().val().values())[0],
					                          "Revenue ( $ / view )": i['revenue'], "Timestamp": i['timestamp']})
				elif i['status'] == 'active':
					dis_name = db.child('distributors').child(i['dis_id']).child("name").get().val()
					app_name = db.child('distributors').child(i['dis_id']).child("app_name").get().val()
					company_name = db.child('distributors').child(i['dis_id']).child("company_name").get().val()
					dis_phone = db.child('distributors').child(i['dis_id']).child("phone").get().val()
					active_contracts.append({"Contract Name ": i['c_name'], "Album Name ":
						list(db.child('albums').child(localId).child(i['alb_id']).get().val().values())[0],
					                         "Revenue ( $ / view )": i['revenue'],
					                         "Activation Time ": i['activation_time'], "Distributor Name ": dis_name,
					                         "App Name ": app_name, "Company Name ": company_name,
					                         "Distributor Contact ": dis_phone})
	return render_template("pro_home.html", names=[name.val()], contracts=str(contract.val()),
	                       ac_contracts=str(ac_contract.val()), views=str(view.val()), revenue=str(rev.val()),
	                       albums=albums, album_arts=album_arts, pending_contracts=pending_contracts,
	                       active_contracts=active_contracts)


@app.route('/dis_home', methods=['GET', 'POST'])
def dis_home():
	localId = session['localId']
	name = db.child('distributors').child(localId).child('name').get()

	available_contracts = []
	active_contracts = []

	contract = 0
	for i in db.child('contracts').get().val().values():
		if i['status'] == 'pending' and str(localId) not in i['dis_id']:
			contract += 1
			available_contracts.append({"Contract Name ": i['c_name'], "Album Name ":
				list(db.child('albums').child(i['pro_id']).child(i['alb_id']).get().val().values())[0],
			                            "Revenue ( $ / view )": i['revenue'], "Timestamp": i['timestamp'],
			                            "Producer Name ": db.child('producers').child(i['pro_id']).get().val()['name']})
	for i in db.child('active_contracts').get().val().values():
		if i['dis_id'] == str(localId):
			active_contracts.append({"Contract Name ": i['c_name'], "Album Name ":
				list(db.child('albums').child(i['pro_id']).child(i['alb_id']).get().val().values())[0],
			                         "Revenue ( $ / view )": i['revenue'], "Activation Time ": i['activation_time'],
			                         "Producer Name ": db.child('producers').child(i['pro_id']).get().val()['name'],
			                         "Current Views": i['views'], "Last Payment Date": i['lastPayTime'],
			                         "Payment Till Date ($)": i['totalPay']})

	ac_contract = db.child('distributors').child(localId).child('active_contracts').get()
	view = db.child('distributors').child(localId).child('views').get()
	rev = db.child('distributors').child(localId).child('revenue').get()
	apiKey = db.child('distributors').child(localId).child('api_key').get().val()

	return render_template("dis_home.html", names=[name.val()], contracts=contract, ac_contracts=str(ac_contract.val()),
	                       views=str(view.val()), revenue=str(rev.val()), available_contracts=available_contracts,
	                       active_contracts=active_contracts, apiKey=apiKey)


@app.route('/create_contract', methods=['GET', 'POST'])
def pro_create_contract():
	if request.method == 'POST':
		c_name = str(request.form.get('c_name', False))
		if db.child("contracts").get().val() != None:
			for i in db.child("contracts").get().val().values():
				print(i.values())
				if c_name in i.values():
					flash('Contract with this name already exists!!', 'error')
					return redirect(url_for('pro_create_contract'))

		email = request.form["email"]
		password = request.form["pass"]
		try:
			user = auth.sign_in_with_email_and_password(email, password)
			localId = user['localId']
		except:
			flash('Incorrect Credentials!', 'error')
			return redirect(url_for('pro_create_contract'))

		alb_name = request.form["alb_name"]
		all_albs = db.child("albums").child(user["localId"]).get()
		for i in all_albs.each():
			if alb_name in i.val().values():
				alb_id = i.key()

		pro_id = user["localId"]
		timestamp = str(datetime.datetime.now())
		rev = float(request.form["revenue"])
		if rev > 1 or rev < 0:
			flash('Enter revenue between 0 and 1!', 'error')
			return redirect(url_for('pro_create_contract'))

		db.child("contracts").push(
			{"c_name": c_name, "alb_id": alb_id, "timestamp": timestamp, "pro_id": pro_id, "status": "pending",
			 "revenue": rev, "dis_id": "blank"})

		flash('New Contract Successfully Uploaded!', 'info')

		contract = int(db.child('producers').child(localId).child('contracts').get().val())
		db.child('producers').child(localId).child("contracts").set(contract + 1)

		return redirect(url_for('pro_home'))

	albums = []
	localId = session.get('localId', None)
	if db.child('albums').child(localId).get().val().values():
		for i in db.child('albums').child(localId).get().val().values():
			albums.append(i['album_name'])
	return render_template("create_contract.html", albums=albums)


@app.route('/add_album', methods=['GET', 'POST'])
def pro_add_album():
	if request.method == 'POST':
		email = str(request.form.get('email', False))
		alb_name = str(request.form.get('alb_name', False))
		password = request.form.get('pass', False)
		no_songs = request.form.get('no_songs', False)
		alb_art = request.form.get('alb_art', False)
		song_files = request.files.getlist('song_files[]')
		try:
			user = auth.sign_in_with_email_and_password(email, password)
			localId = user['localId']
			search_album = db.child('albums').child(localId).get()
			if search_album.val() != None:
				for i in search_album.val().values():
					if alb_name in i.values():
						flash('Album with this name already exists!!', 'error')
						return redirect(url_for('pro_add_album'))
		except:
			flash('Incorrect Credentials!', 'error')
			return redirect(url_for('pro_add_album'))

		if allowed_file(alb_art):
			save = storage.child(localId).child("album_arts").child(alb_name).put(alb_art, localId)

		else:
			save = storage.child(localId).child("album_arts").child(alb_name).put(
				"/root/Desktop/BlockchainInMusic/default.jpg", localId)

		for file in song_files:
			if file and allowed_file(file.filename):
				filename = secure_filename(file.filename)
				storage.child(localId).child("song_files").child(filename).put(filename, localId)
			else:
				flash('This file format is not supported!', 'error')
				return redirect(url_for('pro_add_album'))
		db.child('albums').child(localId).push(
			{"album_name": alb_name, "no_songs": no_songs, "timestamp": str(datetime.datetime.now())})
		n = int(db.child('producers').child(localId).child('albums').get().val())
		db.child('producers').child(localId).child('albums').set(n + 1)

		flash('New Album Successfully Uploaded!', 'info')
		return redirect(url_for('pro_home'))

	return render_template("add_album.html")


@app.route('/accept_contract', methods=['GET', 'POST'])
def dis_accept_contract():
	if request.method == 'POST':
		c_name = str(request.form.get('contract_name', False))
		if c_name == '-- select an option --':
			flash('No Contract was Selected !', 'error')
			return redirect(url_for('dis_accept_contract'))

		email = request.form["email"]
		password = request.form["pass"]
		try:
			user = auth.sign_in_with_email_and_password(email, password)
			localId = user['localId']
		except:
			flash('Incorrect Credentials!', 'error')
			return redirect(url_for('dis_accept_contract'))

		for i in db.child('contracts').get().each():
			if i.val()['c_name'] == c_name:
				key = i.key()
				pro_id = i.val()['pro_id']
				alb_id = i.val()['alb_id']
				rev = i.val()['revenue']
				dis_id = i.val()['dis_id']

		# db.child('contracts').child(key).child("dis_id").set(localId)
		# db.child('contracts').child(key).child("status").set("active")
		# db.child('contracts').child(key).child("activation_time").set(str(datetime.datetime.now()))
		if dis_id == "blank":

			dis_id = []
			dis_id.append(str(localId))
		db.child('contracts').child(key).child("dis_id").set(dis_id)
		db.child('active_contracts').push(
			{"c_name": c_name, "alb_id": alb_id, "activation_time": str(datetime.datetime.now()), "pro_id": pro_id,
			 "status": "active", "revenue": rev, "dis_id": localId, "views": 0, "lastPayTime": "None", "totalPay": 0})

		ac_contracts = int(db.child('distributors').child(localId).child("active_contracts").get().val())
		db.child('distributors').child(localId).child("active_contracts").set(ac_contracts + 1)

		dis_contracts = int(db.child('distributors').child(localId).child("contracts").get().val())
		db.child('distributors').child(localId).child("contracts").set(dis_contracts + 1)

		pro_ac_contracts = int(db.child('producers').child(pro_id).child("active_contracts").get().val())
		# pro_contracts=int(db.child('producers').child(pro_id).child('contracts').get().val())
		db.child('producers').child(pro_id).child('active_contracts').set(pro_ac_contracts + 1)
		# db.child('producers').child(pro_id).child('contracts').set(pro_contracts-1)

	###################################################################################################
		transaction_str = c_name + pro_id + localId + alb_id + str(rev)
		add_transaction(transaction_str)

	####################################################################################################

		flash('Contract accepted Successfully! \n NOTE - Contract is now Active!', 'info')

		return redirect(url_for('dis_home'))

	contracts = []
	albums = []
	artists = []
	rev = []
	localId = session.get('localId', None)
	if db.child('contracts').get().val().values():
		for i in db.child('contracts').get().val().values():
			if i['status'] == 'pending' and str(localId) not in i['dis_id']:
				contracts.append(i['c_name'])
				albums.append(list(db.child('albums').child(i['pro_id']).child(i['alb_id']).get().val().values())[0])
				artists.append(db.child('producers').child(i['pro_id']).get().val()['name'])
				rev.append(i['revenue'])

	return render_template("accept_contract.html", albums=albums, contracts=contracts, artists=artists, revenue=rev)


@app.route('/access_albums', methods=['GET', 'POST'])
def dis_access_albums():
	if request.method == 'POST':
		alb_name = str(request.form.get('album_name', False))
		alb_id = str(request.form.get('alb_id', False))
		art_name = str(request.form.get('art_name', False))

		if alb_name == False:
			flash('No Album was Selected !', 'error')
			return redirect(url_for('dis_access_albums'))

		localId = session.get('localId', None)

		for i in db.child('active_contracts').get().each():
			if i.val()['alb_id'] == alb_id:
				pro_id = i.val()['pro_id']
				c_views = int(i.val()['views'])
				c_id = i.key()

		pro_views = int(db.child('producers').child(pro_id).child('views').get().val())
		db.child('producers').child(pro_id).child('views').set(pro_views + 1)

		dis_views = int(db.child('distributors').child(localId).child('views').get().val())
		db.child('distributors').child(localId).child('views').set(dis_views + 1)

		db.child('active_contracts').child(c_id).child('views').set(c_views + 1)

		flash('Album access Generated! \n NOTE - Views have increased!', 'info')

		return redirect(url_for('dis_home'))

	album_names = []
	album_ids = []
	art_name = []
	localId = session.get('localId', None)
	if db.child('active_contracts').get().val().values():
		for i in db.child('active_contracts').get().val().values():
			if i['dis_id'] == str(localId):
				album_ids.append(i['alb_id'])
				art_name.append(db.child('producers').child(i['pro_id']).child('name').get().val())
				album_names.append(
					db.child('albums').child(i['pro_id']).child(i['alb_id']).child('album_name').get().val())

	return render_template("dis_access_albums.html", album_names=album_names, album_ids=album_ids, art_name=art_name)


@app.route('/dis_pay_pro', methods=['GET', 'POST'])
def dis_payment():
	if request.method == 'POST':
		# alb_name=str(request.form.get('alb_name', False))
		c_id = str(request.form.get('contractId', False))
		# art_name=str(request.form.get('art_name', False))
		c_name = request.form.get('contract_name', False)
		revenue = float(request.form.get('revenue_toPay', False))
		# views=int(request.form.get('views', False))
		print(c_id, c_name, revenue)

		if c_name == False:
			flash('No Contract was Selected !', 'error')
			return redirect(url_for('dis_payment'))

		if int(revenue) < 1:
			flash('Minimum 1$ Payment is allowed!', 'error')
			return redirect(url_for('dis_payment'))

		localId = session.get('localId', None)

		for i in db.child('active_contracts').get().each():
			if i.key() == c_id:
				pro_id = i.val()['pro_id']
				totalPay = float(i.val()['totalPay'])

		pro_rev = float(db.child('producers').child(pro_id).child('revenue').get().val())
		db.child('producers').child(pro_id).child('revenue').set(pro_rev + revenue)

		dis_rev = float(db.child('distributors').child(localId).child('revenue').get().val())
		db.child('distributors').child(localId).child('revenue').set(dis_rev + revenue)

		db.child('active_contracts').child(c_id).child('views').set(0)
		db.child('active_contracts').child(c_id).child('lastPayTime').set(str(datetime.datetime.now()))
		db.child('active_contracts').child(c_id).child('totalPay').set(totalPay + revenue)

		flash('Payment SUCCESS! \n NOTE - Contract Views have been reset!', 'info')

		return redirect(url_for('dis_home'))

	c_names = []
	c_ids = []
	art_name = []
	album_names = []
	revenue = []
	views = []
	art_name = []
	localId = session.get('localId', None)
	if db.child('active_contracts').get().val().values():
		for i in db.child('active_contracts').get().each():
			if i.val()['dis_id'] == str(localId):
				c_names.append(i.val()['c_name'])
				c_ids.append(i.key())
				art_name.append(db.child('producers').child(i.val()['pro_id']).child('name').get().val())
				album_names.append(db.child('albums').child(i.val()['pro_id']).child(i.val()['alb_id']).child(
					'album_name').get().val())
				views.append(i.val()['views'])
				rev = float(float(i.val()['revenue']) * float(i.val()['views']))
				revenue.append(rev)

	return render_template("dis_pay_pro.html", c_names=c_names, c_ids=c_ids, art_name=art_name, album_names=album_names,
	                       views=views, revenue=revenue)



###################################################################

@app.route('/sendnodes', methods=['POST', 'GET'])
def register_new_nodes():
	# nodes_set.add(request.host_url)
	nodes_set.add(request.get_json()["node_address"])
	response = {
		'nodes': list(nodes_set),
		'length': len(nodes_set),
	}

	return jsonify(response), 200


@app.route('/semaphore', methods=['POST', 'GET'])
def semaphore_update():
	# nodes_set.add(request.host_url)
	transactionId = request.get_json()["transaction_id"]
	if transactionId not in semaphore.keys():
		semaphore[transactionId] = 1
		response = {
			'entry': True
		}
		return jsonify(response), 200
	else:
		semaphore[transactionId] += 1
		if semaphore[transactionId] == len(nodes_set):
			semaphore.pop(transactionId)

		response = {
			'entry': False
		}
		return jsonify(response), 200


@app.before_first_request
def activate_job():
	def run_job():
		while True:
			print("Thread Started")
			generate_block()
			sleep(3)

	thread = threading.Thread(target=run_job)
	thread.start()
########################################################################

if __name__ == '__main__':
	app.run(debug=True)
