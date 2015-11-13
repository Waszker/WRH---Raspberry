#!/bin/python2
from WebApiClient import *

print "Witaj w skrypcie rejestrujacym urzadzenie RaspberryPi"
username = raw_input("Podaj nazwe uzytkownika: ")
password = raw_input("Podaj haslo: ")
name = raw_input("Podaj nazwe (np. Raspberak w kuchni)")
print "Podaj kolor, ktory bedzie wyswietlany w aplikacjach. "
color = raw_input("Podaj jako HEX (np. #FF0000): ")

print 'Zaczynam probe rejestracji.'
(status_code, result_content) = register_device(username, password, name, color)
print 'Skonczylem probe.'

if (int(status_code) == Response.STATUS_OK):
    print 'Udalo sie!' + str(result_content)
else:
    print 'Nie udalo sie. Status code: ' + str(status_code)
    print 'Content: ' + str(result_content)





print('Koniec dzialania skryptu.')
