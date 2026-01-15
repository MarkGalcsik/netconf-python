"""
Készítette: Galcsik Márk
Feladat: Csatlakozás a felhasználótól kapott tetszőleges IP címmel rendelkező NetConf szerverre és különböző műveletek elvégzése.
"""
import ipaddress
import sys
import getpass
from ncclient import manager
import xml.dom.minidom
from datetime import datetime

PORT = 830

#Csatlakozási adatok bekérése és validálása.
def get_connection_details():
    connection_data = {}
    
    print("\n--- Csatlakozási adatok megadása ---\n")

    while True:
        ip_input = input("NETCONF szerver IP címe (q - kilépés): ").strip()
        
        if ip_input.lower() == 'q':
            return None
            
        try:
            ipaddress.ip_address(ip_input)
            connection_data['host'] = ip_input
            break
        except ValueError:
            print(f"HIBA: A(z) '{ip_input}' nem érvényes IP cím formátum.")


    while True:
        user = input("Felhasználónév: ").strip()
        if user:
            connection_data['username'] = user
            break
        print("HIBA: A felhasználónév nem lehet üres!")

    password = getpass.getpass("Jelszó: ")
    connection_data['password'] = password
        
    return connection_data

#XML formázása
def get_formatted_xml(xml_string):
    parsed = xml.dom.minidom.parseString(xml_string)
    return parsed.toprettyxml(indent="  ")

#NetConf szerver által támogatott képességek listázása
def get_capability(session):
    try:
        for capability in session.server_capabilities:
            print(capability)
    except Exception as e:
        print(f"Hiba: {e}")

#Teljes running konfiguráció lekérése az eszközről
def get_config(session):
    try:
        netconf_reply = session.get_config(source='running')

        config_file = get_formatted_xml(netconf_reply.data_xml)

        print(config_file)
    
    except Exception as e:
        print(f"Hiba: {e}")

#Szűrők különböző konfigurációs részekhez
#A native szűrő Cisco-specifikus
filters = {
    "interfaces": """
        <interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
            <interface></interface>
        </interfaces>
    """,
    "system": """
        <system xmlns="urn:ietf:params:xml:ns:yang:ietf-system">
        </system>
    """,
    "native": """
        <native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
        </native>
    """,
    "routing": """
        <routing xmlns="urn:ietf:params:xml:ns:yang:ietf-routing">
        </routing>
    """
}

#Szűrt konfiguráció lekérése. 
#Lehetővé teszi specifikus konfigurációs területek lekérdezését. 
def get_filtered_config(session):
    user_filter = input(f"Adjon meg egy filtert {', '.join(filters.keys())}: ").strip().lower()

    if user_filter not in filters:
        print("\nÉrvénytelen megnevezés!\n")
        return
    
    try:
        netconf_reply = session.get_config(
            source='running', 
            filter=('subtree', filters[user_filter]))
        
        print(get_formatted_xml(netconf_reply.data_xml))
    except Exception as filter_err:
        print(f"Hiba a szűrésnél: {filter_err}")


#Running konfiguráció mentése XML fájlba a mai nap dátumával.
def save_config(session):
    try:
        netconf_reply = session.get_config(source='running')

        config_file = get_formatted_xml(netconf_reply.data_xml)

        fajl_nev = f"backup_config_{datetime.now().strftime('%Y%m%d')}.xml"

        with open(fajl_nev, 'w', encoding = 'utf-8') as f:
            f.write(config_file)

        print("\nSikeres mentés!\n")
    except Exception as e:
        print(f"Hiba: {e}")


MENU = {
    '1': ('Szerverfunkciók lekérdezése', get_capability),
    '2': ('Konfiguráció lekérdezése', get_config),
    '3': ('Konfiguráció szűrése', get_filtered_config),
    '4': ('Konfiguráció mentése', save_config)
}

def display_menu():
    for key, (description, _) in MENU.items():
        print(f"{key}. {description}")
    print("q - Kilépés")

def connect_and_operate():    

    connection_params = get_connection_details()

    if connection_params is None:
        print("Kilépés a programból.")
        sys.exit(0)

    try:
        print(f"\nCsatlakozás ide: {connection_params['host']}...")
        
        with manager.connect(
            host=connection_params['host'], 
            port=PORT, 
            username=connection_params['username'], 
            password=connection_params['password'],
            hostkey_verify=False,
            device_params={'name': 'csr'},
            timeout = 60
        ) as m:
            
            print("Sikeres kapcsolat!")

            while True:
                display_menu()
                valasz = input("Válasz: ").strip().lower()

                if valasz == 'q':
                    print("Kilépés...")
                    break

                elif valasz in MENU:
                    _, function = MENU[valasz]
                    function(m)
                    
                
                else:
                    print("Nem megfelelő!")

                        
    except Exception as e:
        print(f"\n[Hiba]: {e}")


if __name__ == '__main__':
    connect_and_operate()