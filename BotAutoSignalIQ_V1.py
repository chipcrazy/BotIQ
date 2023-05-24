from iqoptionapi.stable_api import IQ_Option
from datetime import datetime,  timedelta
from dateutil import tz
#este estaba antes de telegram     from threading import Thread
from threading import Thread, Lock
#para telegram
import json
import requests
#hasta aqui para telegram
import os
import numpy as np
import keyboard
from colorama import Fore, Back, Style, init
import time
import sys
#import getpass
import stdiomask
from os.path import exists as file_exists
import configparser
import re
import unicodedata


'''REVISAR QUE NO VERIFIQUE SI EL PAR ES TRU CUANDO SE ESTA RECORRIENDO PARA PONER EL NRO DE PRECIO 3'''

#ParesRevision = ['EURJPY', 'EURUSD', 'USDCHF','EURGBP', 'USDJPY', 'NZDUSD', 'AUDCAD', 'GBPUSD', 'USDINR', 'GBPJPY', 'USDHKD', 'USDZAR']
ALL_Asset = [] #para recuperar pares y verificar si esta abierto
SaleTelegram = False
EnTelegram = False
CommandoTelegram='' #para decir que se esta ejecutando un comando especial desde telegram

SaleSeñales = False
EjecutandoSeñales = False
					          #,1, 2, 4			
#consevador entradas = [1, 2, 4, 8, 16, 32]
entradas = [1, 2.2, 4.4, 9, 18, 34] # 18 y L36 deberia ser pero para asegurar menos perdida
indice_entradas = 0
gale=1
			#        0        1     2         3         4           5           6         7       8
			#   fecha hora,  par, accion, timeframe, ejecuto, indice precio, indicepar, estado, ParActivo
señales = []
señales_temporal = []
MONTO_AL_ENTRAR = 0.00
MONTO_GANADO = 0.00
MODO ="PRACTICE" #PRACTICE, REAL
MONTO_GAIN = 1.5
MONTO_LOSS = 75
defContaEmail = ""
defContaSenha = ""

configuracion = configparser.ConfigParser()


init(autoreset=True)

#para telegram
global config
token = '5754489037:AAGxDZdrqRL8sbVGacEURAoI6a804QfHhH4'
id_chat = 140163733

#config = {'url': 'https://api.telegram.org/bot{token}/', 'lock': Lock(), 'url_file': 'https://api.telegram.org/bot'}
config = {'url': 'https://api.telegram.org/bot'+token+'/', 'lock': Lock(), 'url_file': 'https://api.telegram.org/bot'}

def transform_Señal(text):
    # Elimina caracteres especiales del texto y emojis
    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode()
    text = re.sub(r'[^\w\s,;:-]', '', text).strip()    
    # Regular expressions to match different formats of the input text
    pattern1 = r'^([Mm]\d{1,2}) (\w{6}(?:-OTC)?) ([Pp][Uu][Tt]|[Cc][Aa][Ll][Ll]) (\d{2}:\d{2})$'
    pattern2 = r'^([Mm]\d{1,2}) (\w{6}(?:-OTC)?) (\d{2}:\d{2}) ([Pp][Uu][Tt]|[Cc][Aa][Ll][Ll])$'
    pattern3 = r'^([Mm]\d{1,2});(\w{6}(?:-OTC)?);([Pp][Uu][Tt]|[Cc][Aa][Ll][Ll]);(\d{2}:\d{2})$'
    pattern4 = r'^([Mm]\d{1,2});(\w{6}(?:-OTC)?);(\d{2}:\d{2});([Pp][Uu][Tt]|[Cc][Aa][Ll][Ll])$'

    # Check which pattern matches the input text
    match = re.match(pattern1, text)
    if match:
        time_frame = match.group(1).upper().replace('M','')
        currency_pair = match.group(2).upper()
        put_call = match.group(3).upper()
        time = match.group(4)
        return f"{time}:00,{currency_pair},{put_call},{time_frame}"

    match = re.match(pattern2, text)
    if match:
        time_frame = match.group(1).upper().replace('M','')
        currency_pair = match.group(2).upper()
        time = match.group(3)
        put_call = match.group(4).upper()
        return f"{time}:00,{currency_pair},{put_call},{time_frame}"

    match = re.match(pattern3, text)
    if match:
        time_frame = match.group(1).upper().replace('M','')
        currency_pair = match.group(2).upper()
        put_call = match.group(3).upper()
        time = match.group(4)
        return f"{time}:00,{currency_pair},{put_call},{time_frame}"

    match = re.match(pattern4, text)
    if match:
        time_frame = match.group(1).upper().replace('M','')
        currency_pair = match.group(2)
        time = match.group(3)
        put_call = match.group(4).upper()
        return f"{time}:00,{currency_pair},{put_call},{time_frame}"

    # If none of the patterns match, return None
    return None

def timestampConverter(time):  
	hora = datetime.strptime(datetime.utcfromtimestamp(time).strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S')
	#hora = hora + timedelta(seconds=2) # ******   incremento 2 segundos para comparar y etrar 2 segundos antes  *******
	hora = hora.replace(tzinfo=tz.gettz('GMT'))

	return str(hora.astimezone(tz.gettz('America/Sao Paulo')))[:-6]

def imprimir_cabecera(texto):
    # Calcula la longitud del texto y la longitud total de la línea
    longitud = len(texto)
    longitud_linea = 80
    
    # Calcula cuántos espacios se deben agregar antes y después del texto para centrarlo
    espacios_antes = (longitud_linea - longitud) // 2
    espacios_despues = longitud_linea - espacios_antes - longitud
    
    # Imprime la línea de cabecera con el texto centrado
    print(Fore.CYAN+Back.LIGHTMAGENTA_EX+"=" * longitud_linea)
    print(" " * espacios_antes + texto + " " * espacios_despues)
    print(Fore.CYAN+Back.LIGHTMAGENTA_EX+"=" * longitud_linea)
    
    
  
#  FUNCIONES DEL MENU  
def mostrar_menu(opciones):    
	print("\033c")
	txt1=''
	txt2=''
	if EjecutandoSeñales:
		txt1 = ' EJECUTANDO SEÑALES '
	if EnTelegram:
		txt2 = ' ACTIVADO MSG EN TELEGRAM '
	if txt1 != '' or txt2 !='':
		imprimir_cabecera(txt2 + txt1)
	print('Seleccione una opción:')
	for clave in sorted(opciones):
		print(Fore.LIGHTRED_EX+f' {clave})'+Fore.LIGHTWHITE_EX+f' {opciones[clave][0]}')


def leer_opcion(opciones):
    while (a := input(Fore.LIGHTYELLOW_EX+'Opción: ')) not in opciones:
        print(Fore.LIGHTRED_EX+'Opción incorrecta, vuelva a intentarlo.')
    return a


def ejecutar_opcion(opcion, opciones):
    opciones[opcion][1]()


def generar_menu(opciones, opcion_salida):
    opcion = None
    while opcion != opcion_salida:
        mostrar_menu(opciones)
        opcion = leer_opcion(opciones)
        ejecutar_opcion(opcion, opciones)
        print()


def menu_principal():
    opciones = {
        '1': ('Cargar Lista de Txt Local', CargarListaLocal),
        '2': ('Cargar Lista de Servidor', CargarListaServer),
        '3': ('Mostrar Lista y Parametros', MostrarListayParametros),
        '4': ('Ejecutar Lista Cargada', EjecutarLista),
        '5': ('Activar Telegram', ActivarTelegram),
        '6': ('Reservado', accion4),        
        '7': ('SALIR', salir)
    }

    generar_menu(opciones, '7')


def MostrarseñalesTelegram():
    Msg = '\n\rSEÑALES........  \n\r'
    Msg = Msg + ' Indice  Entrada   0   1    2   3   4   5\n\r'
    Msg = Msg + ' Tabla Entrada '+str(entradas)+'\n\r\n\r'
    
    for dados in señales:
        if (dados[7][0] == 'E'):
            estadoPar = '🕐'
        if (dados[7][0] == 'W'):
            estadoPar = '✅' + dados[7][1]
        if (dados[7][0] == 'L'):
            estadoPar = '⛔️' + dados[7][1]
        if (dados[7][0] == '0'):
            estadoPar = '🔘' + dados[7][1]
        if (dados[7][0] == 'X'):
            estadoPar = '✘'
              # fecha hora,  par, accion, timeframe, ejecuto, indice precio, indicepar, estado, ParActivo														" Activo="+ str(dados[8])+
        #Msg = Msg + Fore.WHITE+dados[0]+" "+ Fore.LIGHTMAGENTA_EX+dados[1]+ " "+ Fore.YELLOW+dados[2].ljust(4)+ " "+ dados[4]+ " "+ COLOR+dados[7].ljust(2)+ " IndPre="+ dados[5]+  "\n\r"
        Msg = Msg + dados[0][11:]+" "+dados[1]+ " "+ dados[2].ljust(4)+ " "+dados[4]+ " "+ estadoPar.ljust(2)+ " IPre="+ str(dados[5])+  "\n\r"
    Msg = Msg + "\n\rGanancia "+str(round(MONTO_GANADO,2))+'\n\r'
    Thread(target=send_message, args=(Msg, )).start()    
    print(Fore.YELLOW+"\n\rSeñales enviadas a Telegram ", "\r")
    
def estadoCuentaTelegram():
	if EjecutandoSeñales:
		est =">> SEÑALES EJECUTANDOSE <<\n\r"
	else:
		est = ">> SEÑALES PARADAS <<\n\r"
	if (MODO=='PRACTICE'):
		Thread(target=send_message, args=(est+'\n\rCUENTA DE PRACTICA >> Empezando con = '+str(round(MONTO_AL_ENTRAR,2))+"\n\rStop Gain "+str(round(MONTO_GAIN,2))+" Stop Loss "+str(round(MONTO_LOSS,2))+" Gale="+str(gale)+"\n\rGanancia "+str(round(MONTO_GANADO,2)), )).start()
	else:
		Thread(target=send_message, args=(est+'\n\rCUENTA REAL >> Empezando con = '+str(round(MONTO_AL_ENTRAR,2))+"\n\rStop Gain "+str(round(MONTO_GAIN,2))+" Stop Loss "+str(round(MONTO_LOSS,2))+" Gale="+str(gale)+"\n\rGanancia "+str(round(MONTO_GANADO,2)), )).start()		 
 
	#print(Fore.WHITE+Back.BLUE+' ESPERANDO ENTRADA DE LA LISTA... ', end='\n\r')
     
def CargarListaLocal():
	global API,MONTO_AL_ENTRAR
	with open('senal.txt', 'r') as file:
		file_contents = file.read()
	señales_temporal = file_contents.split('\n')
	ii=0
	ahora = timestampConverter(API.get_server_timestamp() ) 
	for sinal in señales_temporal:
        #solo cargar las señales que quedan
		if sinal[:19] >= ahora:
            # ESTO ES SOLO ARA HACER DEMO if (ii<=8):
                            #        0        1     2         3         4           5           6         7       8
                            #   fecha hora,  par, accion, timeframe, ejecuto, indice precio, indicepar, estado, ParActivo
				linea = str( datetime.strptime(sinal[:19], '%Y-%m-%d %H:%M:%S') - timedelta(seconds=2) )+sinal[19:].upper()+",N,0,"+str(ii)+",E,ParActivo" 	#linea = sinal+";N;0;"+str(ii)+";E"
				señales.append(linea.split(','))
				ii=ii+1			
	#ordenar por fecha
	señales2 = sorted(señales, key = lambda x: datetime.strptime(x[0], '%Y-%m-%d %H:%M:%S'))
	indice=0
	for sinall in señales2:
		sinall[6] = indice
		indice=indice + 1
	señales = señales2
 
	CargarParesAbiertosYRevisar()

	word_count = len(señales)
	print("\033c")
	imprimir_cabecera("Cargado Lista local....")
	print(Style.BRIGHT+"\n Cantidad de Señales válidas cargadas >>>> ",word_count)
	Thread(target=send_message, args=('Cantidad de Señales válidas cargadas >>>> '+str(word_count), )).start()

	MONTO_AL_ENTRAR = API.get_balance()
	if MODO=='PRACTICE':
		print(Fore.YELLOW+"\n\rCUENTA DE PRACTICA ","\r")
	else:
		print(Fore.YELLOW+"\n\rCUENTA REAL ","\r")
	print(Fore.LIGHTBLUE_EX+"Empezando con ",str(round(MONTO_AL_ENTRAR,2)),"\r")
	print(Fore.CYAN+"Stop Gain ",str(round(MONTO_GAIN,2)),Fore.CYAN+" Stop Loss ",str(round(MONTO_LOSS,2)),"\r")

	print(Fore.LIGHTBLUE_EX+"Ganancia ",str(round(MONTO_GANADO,2)),"\n\r")


	print('Se Cargo la Lista correctamente, para retornar al menu Presion > ENTER <')
	keyboard.wait('enter')

def CargarListaDeTelegram(LISTA):    
	global API,MONTO_AL_ENTRAR
	global señales
	señales = []
	listaParaCambiar = LISTA.split('\n')
	OperacionHora = 0.00
	data=''
	for linSinal in listaParaCambiar:
		if len(linSinal) < 3:
			OperacionHora = float(linSinal)
		else:														#2023-02-24
			data = data + '\n' + datetime.now().strftime('%Y-%m-%d ')  + transform_Señal(linSinal)
	
	señales_temporal = data.split('\n')
	ii=0
	ahora = timestampConverter(API.get_server_timestamp() ) 
	for sinal in señales_temporal:
        #solo cargar las señales que quedan
		if sinal[:19] != '':
			horasen = datetime.strptime(sinal[:19], '%Y-%m-%d %H:%M:%S')
			if str( horasen - timedelta(hours = (OperacionHora * -1)) ) > ahora:      
							#        0        1     2         3         4           5           6         7       8
							#   fecha hora,  par, accion, timeframe, ejecuto, indice precio, indicepar, estado, ParActivo
				linea = str( datetime.strptime(sinal[:19], '%Y-%m-%d %H:%M:%S') - timedelta(hours = (OperacionHora * -1), seconds=2) )+sinal[19:].upper()+",N,0,"+str(ii)+",E,ParActivo" 	#linea = sinal+";N;0;"+str(ii)+";E"
				señales.append(linea.split(','))
				ii=ii+1			

	#ordenar por fecha
	señales2 = sorted(señales, key = lambda x: datetime.strptime(x[0], '%Y-%m-%d %H:%M:%S'))
	indice=0
	for sinall in señales2:
		sinall[6] = indice
		indice=indice + 1
	señales = señales2
 
	CargarParesAbiertosYRevisar()
 
	word_count = len(señales)
	print("\033c")
	imprimir_cabecera("Cargado Lista de Telegram....")
	print(Style.BRIGHT+"\n Cantidad de Señales válidas cargadas >>>> ",word_count)
	Thread(target=send_message, args=('Cantidad de Señales válidas cargadas >>>> '+str(word_count), )).start()

	MONTO_AL_ENTRAR = API.get_balance()
	if MODO=='PRACTICE':
		print(Fore.YELLOW+"\n\rCUENTA DE PRACTICA ","\r")
	else:
		print(Fore.YELLOW+"\n\rCUENTA REAL ","\r")
	print(Fore.LIGHTBLUE_EX+"Empezando con ",str(round(MONTO_AL_ENTRAR,2)),"\r")
	print(Fore.CYAN+"Stop Gain ",str(round(MONTO_GAIN,2)),Fore.CYAN+" Stop Loss ",str(round(MONTO_LOSS,2)),"\r")

	print(Fore.LIGHTBLUE_EX+"Ganancia ",str(round(MONTO_GANADO,2)),"\n\r")
 
	Thread(target=send_message, args=('LISTA CARGADA VERIFIQUE CON /LISTA \n\r', )).start()
	print('Se Cargo la Lista correctamente....')


 
def CargarListaServer():
	imprimir_cabecera("Cargado Lista Server....(en desarrollo)")    
	print('Has elegido la opción 2')

   
def estadoCuenta():
	if (MODO=='PRACTICE'):
		print(Fore.YELLOW+"\n\rCUENTA DE PRACTICA ","\r")
	else:
		print(Fore.YELLOW+"\n\rCUENTA REAL ","\r")
 
	if EjecutandoSeñales:
		print(Fore.CYAN+">> SEÑALES EJECUTANDOSE <<","\r")
	else:
		print(Fore.CYAN+">> SEÑALES PARADAS <<","\r")
	print(Fore.CYAN+"Empezando con ",str(round(MONTO_AL_ENTRAR,2)),"\r")
	print(Fore.CYAN+"Stop Gain ",str(round(MONTO_GAIN,2)),Fore.CYAN+" Stop Loss ",str(round(MONTO_LOSS,2))," Gale=",str(gale),"\r")
	print(Fore.CYAN+"Ganancia ",str(round(MONTO_GANADO,2)),"\n\r")

	print(Fore.RED+'E '+Fore.WHITE+'EN ESPERA', end='\n')
	print(Fore.GREEN+'W '+Fore.WHITE+'WIN (Ganada)', end='\n')
	print(Fore.RED+'L '+Fore.WHITE+'LOSS (Perdida)', end='\n')
	print(Fore.RED+'00 '+Fore.WHITE+'DOGI (Sin Perdida ni Ganancia)', end='\n')
	print(Fore.RED+'X '+Fore.WHITE+'Cancelado', end='\n')
	print(Fore.WHITE+'El Nro que esta a continuacion de una de estas letras (W ó L) es el Nro de GALE (Maximo '+str(gale)+' Gale)', end='\n')
 
	#print(Fore.WHITE+Back.BLUE+' ESPERANDO ENTRADA DE LA LISTA... ', end='\n\r')

def MostrarListayParametros():
	print("\033c")
	print("\n",Fore.LIGHTBLUE_EX + 'DESARROLLADO POR:  ',Fore.RED+" <=== CHIPCRAZY ===> \r")
	imprimir_cabecera("Lista de Señales....") 
 
	print("\n\r SEÑALES........ \r")
	print(" Indice Precio Entrada",Fore.LIGHTRED_EX+" 0   1    2   3   4   5","\r")
	print(" Tabla Precios Entrada",Fore.LIGHTGREEN_EX+str(entradas),"\r")
	for dados in señales:
		if dados[7][0] == 'W':
			COLOR = Fore.GREEN
		else:                 #        0        1     2         3         4           5           6         7       8
			COLOR = Fore.RED  #   fecha hora,  par, accion, timeframe, ejecuto, indice precio, indicepar, estado, ParActivo
		print(Fore.WHITE+dados[0]," ",Fore.LIGHTMAGENTA_EX+dados[1]," ",Fore.YELLOW+dados[2].ljust(4)," ",dados[4], " ",COLOR+dados[7].ljust(2), " IndicePrecio=",dados[5]," ParActivo=",dados[8],"\r")
  
	estadoCuenta()
 
	print('Mostrando Lista, para retornar al menu Presion > ENTER <')
	keyboard.wait('enter')


def is_empty(a):
    return not bool(a)

def stopWL(lucro, gain,loss):
	global ciclos
	if lucro <= float('-' + str(abs(loss))):
		print('Stop Loss Alcanzado!\n')
		Thread(target=send_message, args=('Stop Loss Alcanzado!'+ str(lucro), )).start()
		ciclos = True
		MostrarseñalesTelegram()
		estadoCuenta()		
		print(Fore.YELLOW+Style.BRIGHT+"\n<<<< PRESIONAR ENTER PARA CERRAR >>>> ")
		keyboard.wait('enter')
		sys.exit()

	if lucro >= float(abs(gain)):
		print('Stop Win Alcanzado!\n')
		Thread(target=send_message, args=('Stop Win Alcanzado!'+ str(lucro), )).start()
		ciclos = True
		MostrarseñalesTelegram()		
		estadoCuenta()	
		print(Fore.YELLOW+Style.BRIGHT+"\n<<<< PRESIONAR ENTER PARA CERRAR >>>> ")
		keyboard.wait('enter')
		sys.exit()

def realiza_entrada(valor, par_moedas, acao_entrada, expiracao, indice, registro, gale):
	status, id = API.buy(valor, par_moedas, acao_entrada, expiracao)
	global MONTO_GANADO
	global entradas
	global señales
	if status:  # 3
		print('ENTRO Binaria: '+par_moedas, acao_entrada+'\n\r')		
		Thread(target=send_message, args=('ENTRO Binaria: '+par_moedas+' '+acao_entrada, )).start()	
		resultado, lucro = API.check_win_v4(id)
		if lucro > 0 :
			print('\n✅ '+resultado+' / LUCRO: '+str(round(lucro, 2)) + ' | ' + str(acao_entrada.upper()) + ' ' + str(par_moedas)+'\n\r')
			registro[7]='W'+str(abs(gale-2)) #estado Win
			indice = 0
			MONTO_GANADO = MONTO_GANADO + round(lucro, 2)
			Thread(target=send_message, args=('\n✅ '+resultado+' / LUCRO: '+str(round(lucro, 2)) + ' | ' + str(acao_entrada.upper()) + ' ' + str(par_moedas), )).start()
		elif lucro == 0:
			print('\nEMPATE | ' + 'LUCRO: $ ' + str(round(lucro, 2)) + ' | ' + str(acao_entrada.upper()) + ' ' + str(par_moedas)+'\n\r')
			registro[7]='0'+str(abs(gale-2))  #estado empatdo
			if (indice < 5 ): #and indice > 0 
				indice = indice + 1
			else:
				indice = 0    
			Thread(target=send_message, args=('\nEMPATE | ' + 'LUCRO: $ ' + str(round(lucro, 2)) + ' | ' + str(acao_entrada.upper()) + ' ' + str(par_moedas), )).start()
		elif lucro < 0:
			print('\n❌ '+resultado+' / LUCRO: '+str(round(lucro, 2)) + ' | ' + str(acao_entrada.upper()) + ' ' + str(par_moedas)+'\n\r')
			registro[7]='L'+str(abs(gale-2)) #estado Loss
			MONTO_GANADO = MONTO_GANADO + round(lucro,2)
			if (indice < 5 ):
				indice = indice + 1
			else:
				indice = 0
			Thread(target=send_message, args=('\n❌ '+resultado+' / LUCRO: '+str(round(lucro, 2)) + ' | ' + str(acao_entrada.upper()) + ' ' + str(par_moedas), )).start()				
			# aqui hay quie revisar el tema de GALE

		if ( resultado =='loose' and gale > 0 ) or ( lucro <= 0  and (gale > 0 and gale < 2)): #aqui modifique hay que revisar el tema de dogi para hacer gale
			registro[5] = indice
			valor_com_martingale = entradas[registro[5]]

			# original valor_com_martingale = (valor * 2.2)
			#self.stopWLM(self.lucro, self.stopWin, self.stopLoss)
			print('\n🔁 MARTINGALE ' + str(gale) + ' | VALOR: $ ' + str(round(valor_com_martingale, 2)) + ' | ' + acao_entrada.upper() + ' ' + par_moedas)
			gale = gale - 1
			Thread(target=realiza_entrada, args=(valor_com_martingale, par_moedas, acao_entrada, expiracao, indice, registro, gale,)).start()
			Thread(target=send_message, args=('\n🔁 MARTINGALE ' + str(gale) + ' | VALOR: $ ' + str(round(valor_com_martingale, 2)) + ' | ' + acao_entrada.upper() + ' ' + par_moedas, )).start()							
			return True
		elif resultado =='loose' and gale == 0:
			#        0        1     2         3         4           5           6         7       8
			#   fecha hora,  par, accion, timeframe, ejecuto, indice precio, indicepar, estado, ParActivo			
			if señales.index(registro) < (len(señales)-1):
				if int(señales[señales.index(registro)][5]) < 5:										# and int(señales[señales.index(registro)+1][5]) < 3
					if señales[señales.index(registro)+1][8] and señales[señales.index(registro)+1][4]=='N':   # tratando de preguntar si esta activo
						señales[señales.index(registro)+1][5] = indice # estaba 3 en todos
					else:
						try:																					# and int(señales[señales.index(registro)+1][5]) < 3
							if señales[señales.index(registro)+2][8] and señales[señales.index(registro)+2][4]=='N':   # tratando de preguntar si esta activo el siguiente
								señales[señales.index(registro)+2][5] = indice
							else:																					# and int(señales[señales.index(registro)+1][5]) < 3
								if señales[señales.index(registro)+3][8] and señales[señales.index(registro)+3][4]=='N':   # tratando de preguntar si esta activo el siguiente
									señales[señales.index(registro)+3][5] = indice
						except:
							pass
				else:
					señales[señales.index(registro)+1][5] = 0

		# eso era antes print('RESULTADO: '+resultado+' / LUCRO: '+str(round(lucro, 2)))

	else:
		print('\n❌ NO ENTRO: '+ ' | ' + str(acao_entrada.upper()) + ' ' + str(par_moedas)+'\n\r')
		Thread(target=send_message, args=('\n❌ NO ENTRO: '+ ' | ' + str(acao_entrada.upper()) + ' ' + str(par_moedas), )).start()			
		# ESTO DE ABAJO ESTAMOS EPERIMENTANDO EN CASO DE QUE PASE si no entra pasar el indice  precio al siguiente
		if señales.index(registro) < (len(señales)-1):
			if int(señales[señales.index(registro)][5]) < 5:										# and int(señales[señales.index(registro)+1][5]) < 3
				if señales[señales.index(registro)+1][8] and señales[señales.index(registro)+1][4]=='N':   # tratando de preguntar si esta activo
					señales[señales.index(registro)+1][5] = señales[señales.index(registro)][5] #3
				else:
					try:																					# and int(señales[señales.index(registro)+1][5]) < 3
						if señales[señales.index(registro)+2][8] and señales[señales.index(registro)+2][4]=='N':   # tratando de preguntar si esta activo el siguiente
							señales[señales.index(registro)+2][5] = señales[señales.index(registro)][5] #3
						else:																					# and int(señales[señales.index(registro)+1][5]) < 3
							if señales[señales.index(registro)+3][8] and señales[señales.index(registro)+3][4]=='N':   # tratando de preguntar si esta activo el siguiente
								señales[señales.index(registro)+3][5] = señales[señales.index(registro)][5] #3
					except:
						pass
			else:
				señales[señales.index(registro)+1][5] = 0


def realiza_entradaDigital(valor, par_moedas, acao_entrada, expiracao, indice, registro, gale): #aun no probado
	global MONTO_GANADO
	global entradas
	global señales
	# Entradas en digital  API.buy(entrada, par, direccion, timeframe)
	status, id = API.buy_digital_spot(par_moedas, valor, acao_entrada, expiracao)

	if isinstance(id, int):
		while True:
			status,lucro = API.check_win_digital_v2(id)
						
			if status:
				print('ENTRO Digital: '+par_moedas, acao_entrada+'\n\r')
				Thread(target=send_message, args=('ENTRO Digital: '+par_moedas+' '+acao_entrada, )).start()	
				if lucro > 0:
					print('\n✅ win / LUCRO-d: '+str(round(lucro, 2)) + ' | ' + str(acao_entrada.upper()) + ' ' + str(par_moedas)+'\n\r')
					registro[7]='W'+str(abs(gale-2)) #estado Win
					indice = 0
					MONTO_GANADO = MONTO_GANADO + round(lucro, 2)
					Thread(target=send_message, args=('\n✅ win / LUCRO-d: '+str(round(lucro, 2)) + ' | ' + str(acao_entrada.upper()) + ' ' + str(par_moedas), )).start()
				elif lucro == 0:
					print('\nEMPATE | ' + 'LUCRO-d: $ ' + str(round(lucro, 2)) + ' | ' + str(acao_entrada.upper()) + ' ' + str(par_moedas)+'\n\r')
					registro[7]='0'+str(abs(gale-2))  #estado empatdo
					if (indice < 5  ): #and indice > 0
						indice = indice + 1
					else:
						indice = 0
					Thread(target=send_message, args=('\nEMPATE | ' + 'LUCRO-d: $ ' + str(round(lucro, 2)) + ' | ' + str(acao_entrada.upper()) + ' ' + str(par_moedas), )).start()					
				elif lucro < 0:
					print('\n❌ loose / LUCRO: '+str(round(lucro, 2)) + ' | ' + str(acao_entrada.upper()) + ' ' + str(par_moedas)+'\n\r')
					registro[7]='L'+str(abs(gale-2)) #estado Loss
					MONTO_GANADO = MONTO_GANADO + round(lucro,2)
					if (indice < 5 ):
						indice = indice + 1
					else:
						indice = 0
					Thread(target=send_message, args=('\n❌ loose / LUCRO: '+str(round(lucro, 2)) + ' | ' + str(acao_entrada.upper()) + ' ' + str(par_moedas), )).start()					

     				# esto es en binaria if ( resultado =='loose' and gale > 0 ) or ( lucro <= 0  and (gale > 0 and gale < 2)): #aqui modifique hay que revisar el tema de dogi para hacer gale
					if lucro <= 0 and gale > 0:			
						registro[5] = indice
						valor_com_martingale = entradas[registro[5]]

						# original valor_com_martingale = (valor * 2.2)
						#self.stopWLM(self.lucro, self.stopWin, self.stopLoss)
						print('\n🔁 MARTINGALE ' + str(gale) + ' | VALOR: $ ' + str(round(valor_com_martingale, 2)) + ' | ' + acao_entrada.upper() + ' ' + par_moedas)
						gale = gale - 1
						Thread(target=realiza_entradaDigital, args=(valor_com_martingale, par_moedas, acao_entrada, expiracao, indice, registro, gale,)).start()
						Thread(target=send_message, args=('\n🔁 MARTINGALE ' + str(gale) + ' | VALOR: $ ' + str(round(valor_com_martingale, 2)) + ' | ' + acao_entrada.upper() + ' ' + par_moedas, )).start()
						return True
					elif lucro < 0 and gale == 0:
						#        0        1     2         3         4           5           6         7       8
						#   fecha hora,  par, accion, timeframe, ejecuto, indice precio, indicepar, estado, ParActivo			
						if señales.index(registro) < (len(señales)-1): #revisar porlomenos un nivel mas o controlar hasta el final de l ista
							if int(señales[señales.index(registro)][5]) < 5:										# and int(señales[señales.index(registro)+1][5]) < 3
								if señales[señales.index(registro)+1][8] and señales[señales.index(registro)+1][4]=='N':   # tratando de preguntar si esta activo
									señales[señales.index(registro)+1][5] = indice
								else:
									try:																					# and int(señales[señales.index(registro)+1][5]) < 3
										if señales[señales.index(registro)+2][8] and señales[señales.index(registro)+2][4]=='N':   # tratando de preguntar si esta activo el siguiente
											señales[señales.index(registro)+2][5] = indice
										else:																					# and int(señales[señales.index(registro)+1][5]) < 3
											if señales[señales.index(registro)+3][8] and señales[señales.index(registro)+3][4]=='N':   # tratando de preguntar si esta activo el siguiente
												señales[señales.index(registro)+3][5] = indice
									except:
										pass
							else:
								señales[señales.index(registro)+1][5] = 0

				break
	else:
		print('\n❌ NO ENTRO: '+ ' | ' + str(acao_entrada.upper()) + ' ' + str(par_moedas)+'\n\r')
		Thread(target=send_message, args=('\n❌ NO ENTRO: '+ ' | ' + str(acao_entrada.upper()) + ' ' + str(par_moedas), )).start()
		# ESTO DE ABAJO ESTAMOS EPERIMENTANDO EN CASO DE QUE PASE si no entra pasar el indice  precio al siguiente
		if señales.index(registro) < (len(señales)-1):
			if int(señales[señales.index(registro)][5]) < 5:										# and int(señales[señales.index(registro)+1][5]) < 3
				if señales[señales.index(registro)+1][8] and señales[señales.index(registro)+1][4]=='N':   # tratando de preguntar si esta activo
					señales[señales.index(registro)+1][5] = señales[señales.index(registro)][5] #3
				else:
					try:																					# and int(señales[señales.index(registro)+1][5]) < 3
						if señales[señales.index(registro)+2][8] and señales[señales.index(registro)+2][4]=='N':   # tratando de preguntar si esta activo el siguiente
							señales[señales.index(registro)+2][5] = señales[señales.index(registro)][5] #3
						else:																					# and int(señales[señales.index(registro)+1][5]) < 3
							if señales[señales.index(registro)+3][8] and señales[señales.index(registro)+3][4]=='N':   # tratando de preguntar si esta activo el siguiente
								señales[señales.index(registro)+3][5] = señales[señales.index(registro)][5] #3
					except:
						pass
			else:
				señales[señales.index(registro)+1][5] = 0

def EjecutarSeñales():
	global SaleSeñales,EjecutandoSeñales
	print(Fore.YELLOW+Back.BLUE+' ESPERANDO ENTRADA DE LA LISTA... ', end='\r')
	while not SaleSeñales:
		ahora = timestampConverter(API.get_server_timestamp() )
		#print(Fore.YELLOW+Back.BLUE+' HORA = ',Fore.YELLOW+Back.BLUE+ahora, end='\r')	
		for dados in señales:
			if dados[0] == ahora and dados[4] == 'N' and dados[8]:
				dados[4] = 'S'
				entrada = entradas[int(dados[5])] # (float(self.spinBox_gerenciamento.value()))*(float(self.spinBox_valueEntry.value()/100))
				par = dados[1]
				direccion = dados[2].lower()
				timeframe = int(dados[3])
				#gale = int(self.spinBox_martingale.value())
				print('\n' + direccion.upper() + ' | ' + par + ' | ' + ahora + ' | ' + str(timeframe)+'M' + '\nSU ENTRADA: $ ' + str(entrada), '\n\r')
				Thread(target=realiza_entrada, args=(entrada, par, direccion, timeframe, int(dados[5]),dados,gale,)).start()
				Thread(target=send_message, args=(direccion.upper() + ' | ' + par + ' | ' + ahora + ' | ' + str(timeframe)+'M' + '\nSU ENTRADA: $ ' + str(entrada), )).start()
			elif dados[0] == ahora and dados[4] == 'N' and is_empty(dados[8]): #aqui es entrada digital
				dados[4] = 'S'
				entrada = entradas[int(dados[5])] # (float(self.spinBox_gerenciamento.value()))*(float(self.spinBox_valueEntry.value()/100))
				par = dados[1]
				direccion = dados[2].lower()
				timeframe = int(dados[3])
				#gale = int(self.spinBox_martingale.value())
				print('\n' + direccion.upper() + ' | ' + par + ' | ' + ahora + ' | ' + str(timeframe)+'M' + '\nSU ENTRADA_d: $ ' + str(entrada), '\n\r')
				Thread(target=realiza_entradaDigital, args=(entrada, par, direccion, timeframe, int(dados[5]),dados,gale,)).start()
				Thread(target=send_message, args=(direccion.upper() + ' | ' + par + ' | ' + ahora + ' | ' + str(timeframe)+'M' + '\nSU ENTRADA_d: $ ' + str(entrada), )).start()

			if (señales[len(señales)-2][4] == 'S' and señales[len(señales)-2][7][0] == 'W') and señales[len(señales)-1][4] == 'N':
				señales[len(señales)-1][4] = 'X'
				señales[len(señales)-1][7] = 'X'
				print('\nTerminando en Positivo y saliendo del Automatizador antes de la ultima entrada', '\n\r')			
				Thread(target=send_message, args=('Terminando en Positivo y saliendo del Automatizador antes de la ultima entrada', )).start()
				Thread(target=MostrarseñalesTelegram, args=()).start()
				print(Fore.YELLOW+Style.BRIGHT+"\n<<<< PRESIONAR ENTER PARA CERRAR >>>> ")
				SaleSeñales=True
				EjecutandoSeñales=False
				keyboard.wait('enter')
				sys.exit()

			stopWL(MONTO_GANADO, MONTO_GAIN,MONTO_LOSS)

										#and ( int(time.strftime("%M")) % 2 != 0)
		if (time.strftime("%S") == '40'):
			RevisaConexionIQ()

		if (time.strftime("%S") == '20') and ( int(time.strftime("%M")) % 2 == 0) and (datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[-6:-3] == '210'):
			if (señales[len(señales)-1][0] > ahora ):
				Thread(target=CargarParesAbiertosYRevisar, args=()).start()
				time.sleep(0.004)

		#if keyboard.is_prDessed("q"):
		if keyboard.is_pressed('shift + esc'):
			estadoCuenta()
			print("\n Saliendo........ \n")
			print("Monto Generado ........ ",round(MONTO_GANADO,2),"\n")
			Thread(target=send_message, args=('Saliendo........ \n'+'Monto Generado ........ '+str(round(MONTO_GANADO,2)), )).start()
			print(Fore.YELLOW+Style.BRIGHT+"\n<<<< PRESIONAR ENTER PARA CERRAR >>>> ")
			SaleSeñales=True
			EjecutandoSeñales=False   
			keyboard.wait('enter')
			break
		if (SaleSeñales):
			break


def EjecutarLista():
    global EjecutandoSeñales, SaleSeñales, MONTO_GANADO
    MONTO_GANADO=0.00
    SaleSeñales=False
    Thread(target=EjecutarSeñales, args=()).start()
    EjecutandoSeñales=True
    Thread(target=send_message, args=('\n 🚀EJECUTANDO SEÑALES⏳ ', )).start()
    print('Ejecutando Señales...')
    
def ActivarTelegram():
    print('Has elegido EjecutarTelegram')
    Thread(target=EscucharTelegram, args=( )).start()

def accion4():
    #keyboard.wait('enter')
    print('Has elegido la opción 6')

def salir():
    global EnTelegram, SaleTelegram
    global SaleSeñales, EjecutandoSeñales
    SaleSeñales = True
    EjecutandoSeñales = False
    time.sleep(1)
    SaleTelegram = True
    EnTelegram = False
    print('Saliendo')
    time.sleep(1)    
    sys.exit()    


    
def del_update(data):
    global config	
    
    config['lock'].acquire()
    requests.post(config['url'] + 'getUpdates', {'offset': data['update_id']+1})
    config['lock'].release()

def send_message(msg):
	global config
	if EnTelegram: 
		config['lock'].acquire()                               #data['message']['chat']['id']
		requests.post(config['url'] + 'sendMessage', {'chat_id': id_chat, 'text': str(msg)})
		#requests.post(config['url'] + 'sendMessage', {'chat_id': id_chat, 'parse_mode': 'HTML', 'text': str(msg)})
		config['lock'].release()
     

def CambiaIndPre(indice):
    global señales
    valores = indice.split('-')
    señales[int(valores[0])-1][5] = valores[1]
    print('indice = ',señales[int(valores[0])-1])
    Thread(target=send_message, args=("Precio nuevo="+str(round(entradas[int(valores[1])],2))+'\n\rPara Indice= '+str(valores[0]) , )).start()

def CambiaModoyRestea(mm):
	global MODO,MONTO_AL_ENTRAR
	global MONTO_GANADO
	global MONTO_GAIN
	global MONTO_LOSS
	try:
		MODO = mm
		API.change_balance(MODO)  # PRACTICE, REAL
		MONTO_AL_ENTRAR = API.get_balance()
		MONTO_GANADO = 0.00
		if (MODO=='PRACTICE'):
			print(Fore.YELLOW+"\n\rCUENTA DE PRACTICA ","\r")
			#msg = "CUENTA DE PRACTICA \n\r Empezando con "+str(round(MONTO_AL_ENTRAR,2))+"\n\rStop Gain "+str(round(MONTO_GAIN,2))+" Stop Loss "+str(round(MONTO_LOSS,2))+" Gale="+str(gale)
			#msg = msg + '\n\r Ganancia '+str(round(MONTO_GANADO,2))			
			#Thread(target=send_message, args=(msg , )).start()			
		else:
			print(Fore.YELLOW+"\n\rCUENTA REAL ","\r")
			#msg = "CUENTA REAL \n\r Empezando con "+str(round(MONTO_AL_ENTRAR,2))+"\n\rStop Gain "+str(round(MONTO_GAIN,2))+Fore.CYAN+" Stop Loss "+str(round(MONTO_LOSS,2))+" Gale="+str(gale)
			#msg = msg + '\n\r Ganancia '+str(round(MONTO_GANADO,2))			
			#Thread(target=send_message, args=(msg , )).start()
   
		estadoCuentaTelegram()
  
		print(Fore.LIGHTBLUE_EX+"Empezando con ",str(round(MONTO_AL_ENTRAR,2)),"\r")
		print(Fore.CYAN+"Stop Gain ",str(round(MONTO_GAIN,2)),Fore.CYAN+" Stop Loss ",str(round(MONTO_LOSS,2))," Gale=",str(gale),"\r")
		print(Fore.LIGHTBLUE_EX+"Ganancia ",str(round(MONTO_GANADO,2)),"\n\r")		
	except:
		Thread(target=send_message, args=('Error al cambiar de Modo', )).start()
		print(Fore.LIGHTBLUE_EX+"Error al cambiar de Modo","\n\r")


def CambiaTP(monto):
	global MONTO_AL_ENTRAR
	global MONTO_GANADO
	global MONTO_GAIN
	global MONTO_LOSS

	MONTO_GAIN = float(monto)
	if (MODO=='PRACTICE'):
		print(Fore.YELLOW+"\n\rCUENTA DE PRACTICA ","\r")
		#msg = "CUENTA DE PRACTICA \n\r Empezando con "+str(round(MONTO_AL_ENTRAR,2))+"\n\rStop Gain "+str(round(MONTO_GAIN,2))+" Stop Loss "+str(round(MONTO_LOSS,2))+" Gale="+str(gale)
		#msg = msg + '\n\r Ganancia '+str(round(MONTO_GANADO,2))			
		#Thread(target=send_message, args=(msg , )).start()			
	else:
		print(Fore.YELLOW+"\n\rCUENTA REAL ","\r")
		#msg = "CUENTA REAL \n\r Empezando con "+str(round(MONTO_AL_ENTRAR,2))+"\n\rStop Gain "+str(round(MONTO_GAIN,2))+Fore.CYAN+" Stop Loss "+str(round(MONTO_LOSS,2))+" Gale="+str(gale)
		#msg = msg + '\n\r Ganancia '+str(round(MONTO_GANADO,2))			
		#Thread(target=send_message, args=(msg , )).start()
	estadoCuentaTelegram()
	print(Fore.LIGHTBLUE_EX+"Empezando con ",str(round(MONTO_AL_ENTRAR,2)),"\r")
	print(Fore.CYAN+"Stop Gain ",str(round(MONTO_GAIN,2)),Fore.CYAN+" Stop Loss ",str(round(MONTO_LOSS,2))," Gale=",str(gale),"\r")
	print(Fore.LIGHTBLUE_EX+"Ganancia ",str(round(MONTO_GANADO,2)),"\n\r")		

def CambiaSL(monto):
	global MONTO_AL_ENTRAR
	global MONTO_GANADO
	global MONTO_GAIN
	global MONTO_LOSS
	
	MONTO_LOSS = float(monto)
	if (MODO=='PRACTICE'):
		print(Fore.YELLOW+"\n\rCUENTA DE PRACTICA ","\r")
		#msg = "CUENTA DE PRACTICA \n\r Empezando con "+str(round(MONTO_AL_ENTRAR,2))+"\n\rStop Gain "+str(round(MONTO_GAIN,2))+" Stop Loss "+str(round(MONTO_LOSS,2))
		#msg = msg + '\n\r Ganancia '+str(round(MONTO_GANADO,2))			
		#Thread(target=send_message, args=(msg , )).start()			
	else:
		print(Fore.YELLOW+"\n\rCUENTA REAL ","\r")
		#msg = "CUENTA REAL \n\r Empezando con "+str(round(MONTO_AL_ENTRAR,2))+"\n\rStop Gain "+str(round(MONTO_GAIN,2))+Fore.CYAN+" Stop Loss "+str(round(MONTO_LOSS,2))
		#msg = msg + '\n\r Ganancia '+str(round(MONTO_GANADO,2))			
		#Thread(target=send_message, args=(msg , )).start()
	estadoCuentaTelegram()
	print(Fore.LIGHTBLUE_EX+"Empezando con ",str(round(MONTO_AL_ENTRAR,2)),"\r")
	print(Fore.CYAN+"Stop Gain ",str(round(MONTO_GAIN,2)),Fore.CYAN+" Stop Loss ",str(round(MONTO_LOSS,2)),"\r")
	print(Fore.LIGHTBLUE_EX+"Ganancia ",str(round(MONTO_GANADO,2)),"\n\r")		

     
def EscucharTelegram():
	global SaleSeñales, EjecutandoSeñales
	global SaleTelegram, EnTelegram
	global CommandoTelegram, entradas #entradas para recuperar las entradas de precios directo
	SaleTelegram = False
	EnTelegram = True
	while not SaleTelegram:
		x = ''
		while 'result' not in x:	
			try:
				x = json.loads(requests.get(config['url'] + 'getUpdates').text)
				if len(x['result']) > 0:
					for data in x['result']:
						Thread(target=del_update, args=(data, )).start()
						if 'document' in data['message']:
							print(json.dumps(data['message'], indent=1))
							#file = get_file(json.loads(requests.post(config['url'] + 'getFile?file_id=' + data['message']['document']['file_id']).text)['result']['file_path'])
							#open(data['message']['document']['file_name'], 'wb').write(file)
						elif data['message']['text'].upper() == 'OTRA PALABRA':
							Thread(target=send_message, args=('Saliendo........ \n'+'Monto Generado ........ '+str(round(MONTO_GANADO,2)), )).start()
							SaleTelegram=True
							break
						elif data['message']['text'].upper() == 'ACTUALIZAR PARES ABIERTOS':
							Thread(target=CargarParesAbiertosYRevisar, args=()).start()          
						elif data['message']['text'].upper()[:6] == 'CAMBIA':
							Thread(target=CambiaIndPre, args=(data['message']['text'].upper()[6:], )).start()
						elif data['message']['text'].upper()[:6] == 'BORRAR': 
							try:  
								señales.pop(int(data['message']['text'].upper()[6:])-1) # EL INDICE HAY QUE RESTAR PARA QUE SEA EL CORRECTO
								Thread(target=send_message, args=("Se elimino el registro indicado" , )).start()
							except:
								Thread(target=send_message, args=("Ocurrio un error y no se elimino el registro indicado" , )).start()
						elif data['message']['text'].upper()[:5] == 'MODO=':
							try:								
								Thread(target=CambiaModoyRestea, args=(data['message']['text'].upper()[5:], )).start()
								#Thread(target=send_message, args=("Se elimino el registro indicado" , )).start()
							except:
								Thread(target=send_message, args=("Ocurrio un error al cambiar de MODO" , )).start()
						elif data['message']['text'].upper()[:8] == 'CANCELAR' and señales[int(data['message']['text'].upper()[8:])-1][4]=='N':
							try:  
								señales[int(data['message']['text'].upper()[8:])-1][4] = 'X'
								señales[int(data['message']['text'].upper()[8:])-1][7] = 'X'
								Thread(target=send_message, args=("Se Cancelo registro " + data['message']['text'].upper()[8:], )).start()
							except:
								Thread(target=send_message, args=("Ocurrio un error y no se cancelo el registro indicado" , )).start()
						elif data['message']['text'].upper()[:3] == 'TP=':
							try:								
								Thread(target=CambiaTP, args=(data['message']['text'].upper()[3:], )).start()								
							except:
								Thread(target=send_message, args=("Ocurrio un error al cambiar el TP" , )).start()
						elif data['message']['text'].upper()[:3] == 'SL=':
							try:								
								Thread(target=CambiaSL, args=(data['message']['text'].upper()[3:], )).start()								
							except:
								Thread(target=send_message, args=("Ocurrio un error al cambiar el SL" , )).start()
						elif data['message']['text'].upper()[:8] == 'PRECIOS=':
							try:
								entradas=eval(data['message']['text'].upper()[8:])
								Thread(target=send_message, args=("Se Cambio Lista de Precios:"+data['message']['text'].upper()[8:] , )).start()
							except:
								Thread(target=send_message, args=("Ocurrio un error al Cargar Precios" , )).start()
           
						elif data['message']['text'].upper()[:1] == '/':
							comando = data['message']['text'].upper()[1:]
							match comando:
								case 'PARAR':
									SaleSeñales=True
									EjecutandoSeñales=False
									Thread(target=send_message, args=('Parando Señales........ \n'+'Monto Generado ........ '+str(round(MONTO_GANADO,2)), )).start()
									break
								case 'INICIAR':
									SaleSeñales=False
									EjecutarLista()
									break
								case 'PARARTELEGRAM':
									SaleTelegram=True
									EnTelegram = False
									Thread(target=send_message, args=('Parando Telegram........ \n'+'Retornando a Consola ........ \n Monto Generado...... '+str(round(MONTO_GANADO,2)), )).start()
									break
								case 'ESTADO':
									estadoCuentaTelegram()
									break
								case 'LISTA':
									MostrarseñalesTelegram()
									break
								case 'CARGARLISTA':
									CommandoTelegram = 'CARGARLISTA'
									Thread(target=send_message, args=('pege la lista de señales la primera fila debe ser diferencia horaria ejem. -1........ \n', )).start()
									break
								case _:
									Thread(target=send_message, args=('Comando no reconocido........ \n', )).start()
							Thread(target=send_message, args=('Comandos:\n\r '+comando+' \n\r', )).start()
						else:
							if CommandoTelegram!='': # PARA VER SI ES ALGUN COMANDO QUE ESTA ESPERANDO RETOALIMENTACION PARA PROCESAR
								match CommandoTelegram:
									case 'CARGARLISTA':
										if data['message']['text'].upper() != 'X':
											CargarListaDeTelegram(data['message']['text'].upper())
											#print('CARGADO: \n\r',data['message']['text'].upper() )
											#Thread(target=send_message, args=('CARGADO: \n\r'+data['message']['text'].upper()+'\n', )).start()
								CommandoTelegram = ''
							else:
								print(json.dumps(data, indent=1))
								Thread(target=send_message, args=('Comandos:\n\r MODO (Modo=PRACTICE - Modo=REAL)\n\r /LISTA \n\r /ESTADO \n\r CAMBIA (CAMBIA1-3 INDICE-NROPRECIO)\n\r ACTUALIZAR PARES ABIERTOS \n\r /CARGARLISTA \n\r /PARAR \n\r /INICIAR \n\r /PARARTELEGRAM \n\r BORRAR (BORRAR1 1=INDICE) \n\r CANCELAR (CANCELAR3)\n\r PRECIOS=[]\n\r', )).start()
					time.sleep(1.5)
     
			except Exception as e:
				x = ''
				pass
				''' if 'Failed to establish a new connection' in str(e):
					print('Perdida de Coexion')
				else:
					print('Error desconocido: ' + str(e))  '''
 


#OPCIONES IQ
def RecuperarParesAbiertos():
	global API
	try:
		global ALL_Asset
		ALL_Asset=API.get_all_open_time()
	except:
		pass

def CargarParesAbiertosYRevisar():
	try:
		print(Fore.CYAN+Back.LIGHTMAGENTA_EX+'\nESPERE VERIFICANDO SI ESTAN ABIERTOS LOS PARES DE LAS SEÑALES!!!')
		RecuperarParesAbiertos()
		for sinal in señales:
				try:
					sinal[8] = ALL_Asset["turbo"][sinal[1]]["open"]
				except:
					pass
		Thread(target=send_message, args=('Actualizo Pares Abiertos', )).start()
	except:
		Thread(target=send_message, args=('NO Actualizo Pares Abiertos', )).start()
  
def RevisaConexionIQ():    
	global API    
	while True:
		if API.check_connect() == False:
			print(Fore.RED+'Upppss, error al conectar....')

			API.connect()
		else:			
			break
		time.sleep(1)


# PROCEDIMIENTOS PRINCIPALES

def CargaConfiguracionesINI():
    global entradas
    global MODO
    global MONTO_GAIN
    global MONTO_LOSS 
    global gale 
    global id_chat
    global defContaEmail
    
    configuracion.read('datosiniciales.ini')
    print('\r           leyendo datosiniciales.ini\n\r')
    if not (file_exists('datosiniciales.ini')): #VIENDO ARCHIVO DE CONFIGURACION
        print('NO EXISTE EL ARCHIVO DE CONFIGURACION datosiniciales.ini', 'ESTE ARCHIVO SERA CREADO!!!\rPorfavor modifique con los datos necesarios\n\r')
        # Añadir sección DEFAULT
        configuracion.add_section('GENERAL')
        configuracion.set('GENERAL', 'email', 'nombre_ejemplo@gmail.com')
        configuracion.set('GENERAL', 'modo', 'PRACTICE')
        configuracion.set('GENERAL', 'precios', '[1, 2.2, 4.8, 9, 18.5, 34.5]')
        configuracion.set('GENERAL', 'stopwin', '1000')
        configuracion.set('GENERAL', 'stoploss', '1000')
        configuracion.set('GENERAL', 'gale', '2')
        configuracion.set('GENERAL', 'activarTelegram', 'True')		

        configuracion.add_section('TELEGRAM')
        configuracion.set('TELEGRAM', 'token', '')
        configuracion.set('TELEGRAM', 'chat_id', '')
        # save to a file
        with open('datosiniciales.ini', 'w') as configfile:
            configuracion.write(configfile)


    print('<< RECUERDE DE TENER LISTO EL ARCHIVO senal.txt ANTES DE ENTRAR AQUI >>\r')
    print('<< SOLO FUNCIONA EN CUENTA DE PRACTICA DE IQOPTIONS >>\r')
    print(Style.BRIGHT+'<< SOLO SE CARGARAN MAXIMO 8 SEÑALES DE SU LISTA >>\r')
    print(Fore.CYAN+'<< INGRESE SU INFORMACION DE IQOPTIONS PARA COMENZAR  >>\r\n')

    if (configuracion['GENERAL']['precios']):
        entradas=eval(configuracion['GENERAL']['precios'])


    #defContaEmail = input(' EMAIL IQ: ')

    if (configuracion['GENERAL']['email']==''):
        defContaEmail = input(' EMAIL IQ: ')
    else:
        defContaEmail = configuracion['GENERAL']['email']
        print(' EMAIL IQ: ',Fore.YELLOW+defContaEmail)

    if (configuracion['GENERAL']['modo'] != ''):
        MODO = configuracion['GENERAL']['modo']

    if (configuracion['GENERAL']['stopwin']):
        MONTO_GAIN=eval(configuracion['GENERAL']['stopwin'])

    if (configuracion['GENERAL']['stoploss']):
        MONTO_LOSS=eval(configuracion['GENERAL']['stoploss'])

    if (configuracion['GENERAL']['gale']):
        gale=eval(configuracion['GENERAL']['gale'])

    if (configuracion['TELEGRAM']['chat_id'] != ''):
        id_chat=eval(configuracion['TELEGRAM']['chat_id'])


def entrarIqoptions():
    global defContaEmail
    global defContaSenha
    global API
    defContaSenha = stdiomask.getpass('\n INGRESE SU PASSWORD :: ', mask='-')
    print('Conectando su cuenta ...')
    API = IQ_Option(defContaEmail, defContaSenha)
    API.connect()
    #API.change_balance(MODO)  # PRACTICE, REAL

    RevisaConexionIQ()
    print(Fore.CYAN+'\nConectado con exito!!!')




    

if __name__ == "__main__":
    CargaConfiguracionesINI()
    entrarIqoptions()
    menu_principal()



