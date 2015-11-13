#!/bin/python2
from WebApiClient.py import *

print "Witaj w skrypcie rejestrujacym urzadzenie RaspberryPi"
username = raw_input("Podaj nazwe uzytkownika: ")
password = raw_input("Podaj haslo: ")
name = raw_input("Podaj nazwe (np. Raspberak w kuchni)")
print "Podaj kolor, ktory bedzie wyswietlany w aplikacjach. "
color = raw_raw_input("Podaj jako HEX (np. #FF0000): ")

print 'Zaczynam probe rejestracji.'
(device_token, result) = WRH.register_device(username, password, name, color)
print 'Skonczylem probe.'

if (result == Response.STATUS_OK):
    print 'Udalo sie!' + str(device_token)
else:
    print 'Nie udalo sie. Status code: ' + str(result)
    print '' + str(device_token)





print('Koniec dzialania skryptu.')
