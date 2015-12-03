#!/usr/bin/python2.7

import json
import threading
import time
import socket
# // import WebApiLibrary

#na sztywno dane rasberaka uzytkownika przem321@wp.pl
deviceid = '9'
devicetoken = 'dea763a0-5c0c-4555-bcc6-9f0cc1dcf030'
temp_cnt = 0

def _read_movement():
	global temp_cnt
	temp_cnt = temp_cnt + 1
	if temp_cnt % 5 == 0:
		return 1
	return 0
	
def main():
	print('main() start')
	while True:
		measurement = _read_movement()
		sleep(10)
	print('main() end')

if __name__ == "__main__":
    main()
