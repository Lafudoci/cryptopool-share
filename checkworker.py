import configparser
import time
import requests
import json

config = configparser.ConfigParser()
config.read('config.ini')

def apirequest(api_url):
	try:    
		resp = requests.get(url=api_url, timeout = 10)
		if str(resp) == '<Response [200]>':
			resp_data = json.loads(resp.text)
			print(api_url[0:24]+'--> Pool APIrequest OK')
			return resp_data
		else:
			print(api_url[0:24]+'--> APIrequest error : Response was not 200')
			return -1
	except requests.exceptions.RequestException as err:
		print(api_url[0:24]+'--> APIrequest error')
		return -2


def calculateCredit(work_credit):
	all_credit = 0
	work_share ={}

	for worker,credit in work_credit.items():		# sum workers's credit
		all_credit += credit
	print('Credit sum: '+ str(all_credit))

	for worker,credit in work_credit.items():		# calculate workers's share
		work_share[worker] = credit/all_credit

	print('Shares percentage in this period:\n'+json.dumps(work_share)+'\n')

	return work_share

def checkPay(pool):
	try:											# read last payment hash from cache
		lp = open( pool+'_pay', 'r')
		lastpay = json.loads(lp.read())
		last_hash = lastpay['Last_hash']
		lp.close()
	except (OSError, IOError) as e:
		print(pool+": Previous payment hash not found")
		last_hash = 'Not yet'

	if pool == 'ethwgpu':							# get last payment hash from ethwgpu pool
		api_url='https://eth-tw.gpumine.org/api/miner/'+ config['eth-tw.gpumine.org']['address']   

		miners_data = apirequest(api_url)

		pay_hash = miners_data['payments'][-1]['tx_hash']
		status = miners_data['payments'][-1]['status']
		paid = miners_data['payments'][-1]['paid']
		if pay_hash != last_hash and status == 'completed' :
			print(pool+': New payment was found!: '+ paid)
			print(pool+': Last payment:\n'+pay_hash)
			last_hash = pay_hash
			last_pay = {'Last_hash':str(last_hash),'paid':paid}
			lp = open(pool+'_pay', 'w')
			lp.write(json.dumps(last_pay))
			lp.close()
			return last_pay
		else:
			print(pool+': Nothing new, last payment:\n'+str(last_hash))
			return -2

	elif pool == 'nanopoolxmr':						# get last payment hash from nanopool
		api_url='https://api.nanopool.org/v1/xmr/payments/'+ config['xmr.nanopool.org']['address']        
		miners_data = apirequest(api_url)

		if miners_data == -2:							# return -1 if API exception error
			print('API HTTP error')
			return -1
		elif miners_data == -1:
			print('API error: '+ miners_data['error'])	# return -1 if http resp not 200
			return -1
		elif miners_data['status'] == False:			# return -1 if resp status false
			print('API error: '+ miners_data['data'])
			return -1
		else: print('Good API Response')

		pay_hash = miners_data['data'][0]['txHash']
		status = miners_data['data'][0]['confirmed']
		paid = miners_data['data'][0]['amount']
		if pay_hash != last_hash and status == True :
			print(pool+': New payment was found!: '+ str(paid))
			print(pool+': Last payment:\n'+pay_hash)
			last_hash = pay_hash
			last_pay = {'Last_hash':str(last_hash),'paid':paid}
			lp = open(pool+'_pay', 'w')
			lp.write(json.dumps(last_pay))
			lp.close()
			return last_pay
		else:
			print(pool+': Nothing new, last payment:\n'+str(last_hash))
			return -2
	else:
		print(pool+': Check payment error')
		return -1



def ethtwgpumine():
	
	api_url='https://eth-tw.gpumine.org/api/miner/'+ config['eth-tw.gpumine.org']['address']   
	miners_data = apirequest(api_url)

	try:
		cd = open('ethtwgpu_credit', 'r')			# read credit from cache
		work_credit = json.loads(cd.read())
		cd.close()
	except (OSError, IOError) as e:
		print('New recording')
		work_credit = {}

	msg = ''
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

	print(time.strftime("======== %Y-%m-%d %H:%M:%S ========", time.localtime()))
	print('Real-time status:\n'+msg)
	
	cd = open('ethtwgpu_credit', 'w')				# write the credit back to cache
	cd.write(json.dumps(work_credit))
	cd.close()

	print('Shares among workers:\n'+json.dumps(work_credit)+'\n')

	return work_credit


def nanopoolxmr():

	api_url='https://api.nanopool.org/v1/xmr/workers/'+ config['xmr.nanopool.org']['address']        
	miners_data = apirequest(api_url)
	#print(miners_data)

	if miners_data == -2:							# return -1 if API exception error
		print('API HTTP error')
		return -1
	elif miners_data == -1:
		print('API error: '+ miners_data['error'])	# return -1 if http resp not 200
		return -1
	elif miners_data['status'] == False:			# return -1 if resp status false
		print('API error: '+ miners_data['data'])
		return -1
	else: print('Good API Response')

	try:
		cd = open('nanopoolxmr_credit', 'r')		# read credit from cache
		work_credit = json.loads(cd.read())
		cd.close()
	except (OSError, IOError) as e:
		print('New recording')
		work_credit = {}

	now = time.time()
	msg = ''
	for worker in miners_data['data']:				# load worker credit from pool
		worker_id  = worker['id']
		hashrate = worker['hashrate']
		shares = worker['rating']
		
		if worker_id not in work_credit:			# add new workers's credit
			work_credit[worker_id] = hashrate
		else:
			credit = work_credit[worker_id]			# add up old worker's credit
			work_credit[worker_id] = credit + hashrate

		msg += ('%s: \t%s H/s.\n' % (worker_id, hashrate) )

	print(time.strftime("======== %Y-%m-%d %H:%M:%S ========", time.localtime()))
	print('Real-time status:\n'+msg)
	
	cd = open('nanopoolxmr_credit', 'w')			# write the credit back to cache
	cd.write(json.dumps(work_credit))
	cd.close()

	print('Total hashs among workers:\n'+json.dumps(work_credit)+'\n')

	return work_credit

if __name__ == '__main__':
    # ethtwgpumine()
    nanopoolxmr()
    # checkPay('ethwgpu')
    checkPay('nanopoolxmr')