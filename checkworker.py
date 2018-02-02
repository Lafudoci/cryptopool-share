import configparser
import requests
import json

config = configparser.ConfigParser()
config.read('config.ini')

def ethtwgpumine():
	all_shares = 0
	msg = ''
	try:
		api_url='https://eth-tw.gpumine.org/api/miner/'+ config['eth-tw.gpumine.org']['address']   
		resp = requests.get(url = api_url, timeout = 10)
		if str(resp) == '<Response [200]>':
			miners_data = json.loads(resp.text)		
			return miners_data
		else:
			print('API error')
			return -1
	except requests.exceptions.RequestException as err:
		print('Requests error')
		return -1


if __name__ == '__main__':
    ethtwgpumine()