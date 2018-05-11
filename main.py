import configparser
import time
import requests
import json
import checkworker

config = configparser.ConfigParser()
config.read('config.ini')

work_share = {}
last_check = 0
final_payout = {}
scan_interval = int(config['general']['scan_interval'])


while(True):
	if ( time.time() - last_check > scan_interval*60):
		
		while(True):
			work_credit = checkworker.nanopoolxmr()		#get and sum worker credit from nanopool
			if work_credit == -1:
				print('Can not get data from pool, will retry in 5s' )
				time.sleep(5)
			else:
				break

		work_share = checkworker.calculateCredit(work_credit)		# calculate workers's share

		while (True):
			payment = checkworker.checkPay('nanopoolxmr')				# check last payment from pool

			if payment == -1:
				print('Can not get payment from pool, will retry in 5s' )
				time.sleep(5)
			else:
				break

		if payment == -2:
			print('Wait next check in '+str(scan_interval)+' mins')

		else:
			for worker,percent in work_share.items():				# divide profit by shares
				final_payout[worker] = float(payment['paid']) * float(percent)
			print('Final payout table:\n'+json.dumps(final_payout))
			print('Wait next check in '+str(scan_interval)+' mins')
			loacal_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

			pay_list = ''
			for worker,pay in final_payout.items():
				pay_list += '%s,%.17f\n'%(worker,pay)

			cd = open('nanopoolxmr_credit', 'r')			# read sample size from cache
			cache_data = json.loads(cd.read())
			sample_size = cache_data['sample_size']
			cd.close()

			pay_sheet = open('payout_share.csv', 'a')
			pay_sheet.write('%s,%s,%d\n%s\n' % (loacal_time, payment['Last_hash'],sample_size, pay_list))
			pay_sheet.close()

			work_credit = {}
			work_share = {}
			all_credit = 0
			final_payout = {}
			sample_size = 0

			cd = open('nanopoolxmr_credit', 'w')			# write the credit back to cache
			cache_data['work_credit'] = work_credit
			cache_data['sample_size'] = sample_size
			cd.write(json.dumps(cache_data))
			cd.close()
			
		last_check = time.time()

time.sleep(5)