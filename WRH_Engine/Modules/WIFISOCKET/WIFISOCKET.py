#!/usr/bin/python2.7

import json
import threading
import time
import socket
# // import WebApiLibrary

#na sztywno dane rasberaka uzytkownika przem321@wp.pl
deviceid = '9'
devicetoken = 'dea763a0-5c0c-4555-bcc6-9f0cc1dcf030'
moduleid = '15'

# UWAGA
# zmiany w planach, nie bedzie modulu od gniazdka.
# poniewaz pomiarow nie zbieramy z gniazdka,
# a wykonaniem steruje bezposrednio Scenario Manager
	

if __name__ == "__main__":
    print('Wifi: Started.')
	while True:
		time.sleep(100)	
	print('Wif: Ended.')
