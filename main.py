import configparser
import time
import requests
import json

import checkworker

config = configparser.ConfigParser()
config.read('config.ini')

last_hash = ''
work_share = {}
last_check = 0
final_payout = {}
scan_interval = int(config['eth-tw.gpumine.org']['scan_interval'])


def calculateCredit(miners_data):
	all_credit = 0
	msg = ''

	try:
		cd = open('credit.json', 'r')				# read credit from cache
		work_credit = json.loads(cd.read())
		cd.close()
	except (OSError, IOError) as e:
		print('New recording\n')
		work_credit = {}

	for worker in miners_data['workers']:			# load worker credit from pool
		worker_id  = worker['rig']
		hashrate24h = worker['hashrate24h']
		shares = worker['validShares']
		
		if worker_id not in work_credit:			# add new workers's credit
			work_credit[worker_id] = shares
		else:
			credit = work_credit[worker_id]			# add up old worker's credit
			work_credit[worker_id] = credit + shares

		msg += ('%s: \t%s, %d shares.\n' % (worker_id, hashrate24h, shares) )
	
	cd = open('credit.json', 'w')					# write the credit back to cache
	cd.write(json.dumps(work_credit))
	cd.close()

	print(time.strftime("\n======== %Y-%m-%d %H:%M:%S ========", time.localtime()))
	print('Real-time status:\n'+msg)


	for worker,credit in work_credit.items():		# calculate workers's share
		all_credit += credit
	print('All_credit: '+ str(all_credit))

	for worker,credit in work_credit.items():		# calculate workers's share
		work_share[worker] = credit/all_credit

	print('Shares among workers:\n'+json.dumps(work_credit)+'\n')
	print('Shares percentage in this period:\n'+json.dumps(work_share)+'\n')

def checkPay(miners_data):
	global last_hash
	try:
		lp = open('lastpay.json', 'r')
		lastpay = json.loads(lp.read())
		last_hash = lastpay['Last_hash']
		lp.close()
	except (OSError, IOError) as e:
		print("Recording last payment hash\n")
		last_hash = ''

	pay_hash = miners_data['payments'][-1]['tx_hash']
	status = miners_data['payments'][-1]['status']
	paid = miners_data['payments'][-1]['paid']
	if pay_hash != last_hash and status == 'completed' :
		print('New payment was found!: '+ paid)
		last_hash = pay_hash
		lp = open('lastpay.json', 'w')
		lp.write(json.dumps({'Last_hash':last_hash}))
		lp.close()
		return paid
	else:
		print('Last payment:\n'+pay_hash)
		return -1



while(True):
	if ( time.time() - last_check > scan_interval*10):
		
		miners_data = checkworker.ethtwgpumine()

		calculateCredit(miners_data)

		payment = checkPay(miners_data)

		if payment != -1:
			for worker,percent in work_share.items():
				final_payout[worker] = float(payment) * float(percent)
			print('Final payout table:\n'+json.dumps(final_payout))
			loacal_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

			pay_list = ''
			for worker,pay in final_payout.items():
				pay_list += '%s,%.17f\n'%(worker,pay)

			pay_sheet = open('payout_share.csv', 'a')
			pay_sheet.write('%s,%s\n%s\n' % (loacal_time, last_hash, pay_list))
			
			pay_sheet.close()

			work_credit = {}
			work_share = {}
			all_credit = 0
			final_payout = {}
		
		last_check = time.time()

time.sleep(1)