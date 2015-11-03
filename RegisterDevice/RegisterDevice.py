import requests
import json

baseaddress = 'https://wildraspberrywebapi.azurewebsites.net/'

print("Skrypt rejestrujacy Urzadzenie Raspberry Pi. ")

username = input("Podaj nazwe uzytkownika: ")
password = input("Podaj haslo: ")
name = input("Podaj nazwe (np. Raspberak w kuchni)")
print("Podaj kolor, ktory bedzie wyswietlany w aplikacjach. ")
color = input("Podaj jako HEX (np. #FF0000): ")
#username = 'test@wp.pl'
#password = '123'
#name = 'raspberry pi'
#color = 'FF0000'


url = baseaddress + 'api/wrh/registerdevice'
content = {'Username': username, 'Password': password, 'Name': name, 'Color': color}
headers = {'content-type': 'application/json'}

print('Zaczynam probe rejestracji.')
response = requests.post(url, data = json.dumps(content), headers = headers)
print('Skonczylem probe.')

if (response.status_code == 200):
    print('Udalo sie!')
else:
    print('Nie udalo sie. Status code: ' + str(response.status_code))
    print(response.text)





print('Koniec dzialania skryptu.')