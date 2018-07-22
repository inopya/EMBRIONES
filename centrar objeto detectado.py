# -*- coding: cp1252 -*-

#         _\|/_
#         (O-O)
# -----oOO-(_)-OOo----------------------------------------------------


#######################################################################
# ******************************************************************* #
# *                                                                 * #
# *                   Autor:  Eulogio López Cayuela                 * #
# *                                                                 * #
# *         Utilidad para orientar robot hacia un objeto            * #
#*               detectado por la camarala camara                   * #
# *                                                                 * #
# *                  Version 1.1   Fecha: 21/07/2018                * #
# *                                                                 * #
# ******************************************************************* #
#######################################################################

'''
NOTAS:
    - pyton 2.7
    - SimpleCV


Deteccion/Seguimiento de un objeto circular de color determinado.
El programa presupone que los servos estan conectados a Arduino o similar
y el control de imagen se comunica mediante puerto serie con la parte motiz
Si los servos estan conectados a las Raspberry,
las funciones de puerto serie son innecesarias

Usa el BOTON DERECHO sobre la imagen para intercambiar la visualizacion
entre el modo Normal (la captura de la camara) o la Imagen Tratada

Pulsando con el BOTON IZQUIERDO seleccionamos el nuevo color objetivo
El programa trada de encontrar un valor promedio para el color usando la zona adyacente,
de no ser posible se utiliza como color objetivo el del pixel sobre el que se ha pulsado.
 
'''

print __doc__


import SimpleCV
#--------------------------------------------------------
# IMPORTACION DE MODULOS
#--------------------------------------------------------

import sys         #Conocer el tipo de sistema operativo
import time        #manejo de funciones de tiempo (fechas, horas, pausas...)
import serial      #libreria Serial para comunicar con Arduino

from SimpleCV import Image, Camera, Color, DrawingLayer, Display
import numpy as np
import math




#====================================================================================================
#  INICIO DEL BLOQUE DEFINICION DE VARIABLES GLOBALES y CONSTANTES PARA EL PROGRAMA 
#====================================================================================================


COLOR_OBJETIVO = (255,30,30)  #como referencia se busca un objeto rojo. Se puede seleccionar con BOTON IZQUIERDO un colo de la imagen

# Parametros para las tolerancias de la funcion esCirculo() 
toleranciaWH = 0.15 # 0.15 Tolerancia para mi funcion que localiza los circulos con el 'AspectRadio' del blob
desviacionD = 0.25   # 0.25 desviacion para la funcion interna circleDistance()
toleranciaLP = 0.15 # 0.15 Ratio entre la Longitud del circulo ideal y el perimetro real del blob


resolucion = (320,240)

cx = 0                                              # variable que contendra la coordenada x del ojbeto que sirve como referencia
centro_frame = int(resolucion[0]/2)                 # la mitas del ancho de frame que estoy usando
margen_Centro = int(3.0*(resolucion[0]/100))        # 3% del ancho de frame es el margen que permito (en pixels) respecto al centro



#algunas variables para el control de las detecciones
DILATE = 1         #cantidad de dilate ue se aplicara a la imagen (0-xx)
Umbral_bajo = 200  #limite inferior y superior para
Umbral_alto = 255  #la aplicacion de  stretch()

FLAG_mostrar_tratada = False    #Si es True muestra la imagen con los filtros aplicados, False muestra la imagen real de la camara (BOTON DERECHO)
FLAG_colorMode_HUE = False       #activar para trabajar en modo HUE, util para evitar los problemas con cambios de iluminacion 
                                #no recomendado lara localizar objetos blancos o negros            
FLAG_isCircle = True           #Si es False se utiliza la funcion interna isCircle(). True se usa la funcion de usuario esCirculo()

#----------------------------------------------------------------------------------------------------
#    FIN DEL BLOQUE DE DEFINICION DE VARIABLES GLOBALES y CONSTANTES PARA EL PROGRAMA 
#----------------------------------------------------------------------------------------------------





#====================================================================================================
# INICIO DEL BLOQUE DE DEFINICION DE FUNCIONES
#====================================================================================================

def detectar_PuertoSerie():
    '''
    Funcion para facilitar la deteccion del puerto Serie en distintos sistemas operativos
    Escanea los posibles puertos y retorna el nombre del puerto con el que consigue comunicarse
    '''

    #Reconocer el tipo de sistema operativo
    sistemaOperativo = sys.platform
    
    #Definir los prefijos de los posibles puertos serie disponibles tanto en linux como windows
    puertosWindows = ['COM']
    puertosLinux = ['/dev/ttyUSB', '/dev/ttyACM', '/dev/ttyS', '/dev/ttyAMA','/dev/ttyACA']
    
    puertoSerie = None
    if (sistemaOperativo == 'linux2'):
        listaPuertosSerie = puertosLinux
    else:
        listaPuertosSerie = puertosWindows

    for puertoTestado in listaPuertosSerie:
        for n in range(20):
            try:
                # intentar crear una instancia de Serial para 'dialogar' con ella
                nombrePuertoSerie = puertoSerie+'%d' %n
                serialTest = serial.Serial(nombrePuertoSerie, 9600)

                '''  este bloque es opcional por si queremos por ejempo, que ante varios dispositivos conectados
                obtener el nombre del puerto en el que hay uno en concreto que estemos buscando.
                Cosa que podemos hacer dialogando con el y esperando una respuesta conocida
                '''
##                datos_recibidos = None
##                datos_recibidos = consultar_PuertoSerie(serialTest, "dato de muestra")
##                serialTest.close()
##                if datos_recibidos == "patron deseado":
##                    return puertoSerie

                #devolver el primer puerto disponible. Si queremos devolver uno en concreto, comentar estas dos lineas y descomentar el bloque anterior
                serialTest.close()
                return puertoSerie

            except Exception as e:
                pass
                #descomentar si se desea conocer el eror (obviamente es que el puerto no esta disponible)
                #print e
        
    return None #si llegamos a este punto es que no hay puerto serie disponible

#-----------------------------------------------------------------------------------------  

def consultar_PuertoSerie(SerialPort, peticion): # con esta notacion: b'*') --> El prefijo b (byte) es opcional en python 2.x pero obligatorio en 3.x
    '''
    Funcion para acceso a PuertoSerie y obtencion de datos
    version mejorada para evitar errores de comunicacion
    ante eventuales fallos de la conexion.
    '''
    
    datos_leidos_en_SerialPort = None
    
    try:
        SerialPort.flushInput()         # flush input buffer, eliminar posibles restos de lecturas anteriores
        SerialPort.flushOutput()        # flush output buffer, abortar comunicaciones salientes que puedan estar a medias

    except Exception as e:
        print("error borrando datos del puerto Serie\n",e)
 

    # ** INICIO bloque de consulta  ** 
    try:
        if peticion != None:
            sendTo_puertoSerie(SerialPort, peticion)
            #pausa opcional para dar tiempo al puerto (con arduino es util)
            time.sleep(0.25)                    

        # revisar si hay datos en el puerto serie
        if (SerialPort.inWaiting()>0):
            #leer una cadena desde el el puerto serie
            datos_leidos_en_SerialPort = SerialPort.readline() 
            try:
                pass
                #este try es por si se desea procesar/comprobar los datos leidos antes de devolverlos

            except Exception as e:
                print("Datos no validos")
                return None

    except Exception as e:
        print("\n == CONEXION PERDIDA == ")


    return datos_leidos_en_SerialPort

#-----------------------------------------------------------------------------------------  

def sendTo_puertoSerie(puertoSerie, dato):
    try:
        puertoSerie.flushInput() #flush input buffer, eliminar posibles restos de lecturas anteriores
        puertoSerie.flushOutput()#flush output buffer, abortar comunicaciones salientes que puedan estar a medias
        puertoSerie.write(str(dato).encode())
    except Exception as e:
        pass 
        #Descomentar para mostar error
        #print ("ERROR enviando datos")
        #print (e)
 

#-----------------------------------------------------------------------------------------

def esCirculo(b, toleranciaWH, toleranciaLP, desviacionD):

    '''
    funcion ligeramente modificada para que no devuelva el codigo de error
    -- b: blob que queremos certificar como circulo

    -- toleranciaWH: Ratio de los valores Alto y Ancho del blob.
    -- toleranciaLP: ratio entre la longitud del circulo ideal y el
       perimetro real del blob
    -- desviacionD: Desviacion del circulo ideal.
    '''
    

    aspectRadio = float(b.height())/ float(b.width())
    if aspectRadio > (1 + toleranciaWH) or aspectRadio < (1 - toleranciaWH):
        if aspectRadio > 1:
            aspectRadio -= 1
        else:
            aspectRadio = 1 - aspectRadio
        return (False)#,'WH ' + str(aspectRadio)[:4])
    if b.circleDistance() > desviacionD:
        return(False)#,'D ' + str(b.circleDistance())[:4])
    # longitudIdeal: Longitud que tendria el perimetro del objeto
    # si fuese una circunferencia de radio el radio medio devuelto
    # por blob.radius()
    longitudIdeal = 2 * 3.1415627 * b.radius()
    perimetro = b.perimeter()
    ratioLP = float(longitudIdeal / perimetro)
    if ratioLP > (1 + toleranciaLP) or ratioLP < (1 - toleranciaLP):
        if ratioLP > 1:
            ratioLP -= 1
        else:
            ratioLP = 1 - ratioLP
        return (False)#, 'LP ' + str(ratioLP)[:4])
    return (True)#,'OK')
#----------------------------------------------------------------------------------------------------
#  FIN DEL BLOQUE DE DEFINICIONN DE FUNCIONES
#----------------------------------------------------------------------------------------------------




#crear un puerto serie para la comunicacion, si encontramos puerto didponible
puertoDetectado = detectar_PuertoSerie() #detectamos automaticamente el puerto

if (puertoDetectado != None):
    mi_puerto_Serie = serial.Serial(puertoDetectado, 9600) #usamos el puerto detectado
    print (" ** DISPOSITIVO CONECTADO EN " + puertoDetectado + " ** ")
else:
    print (" == DISPOSITIVO NO PRESENTE == ")


'''
Quitar "or puertoDetectado == None" de la condicion una vez que el sistema este conectado al servo que hay que controlar 
'''

if (puertoDetectado != None or puertoDetectado == None):

    display = Display() #necesario en este caso para poder acceder a metodos relacionados con el raton (posicion y pulsaciones)
    webcam = Camera()


    while display.isNotDone():

        captura = webcam.getImage().resize(resolucion[0],resolucion[1])

        if display.mouseRight:
            FLAG_mostrar_tratada = not(FLAG_mostrar_tratada)

        if display.mouseLeft:
            pixel_x, pixel_y = display.mouseRawX, display.mouseRawY 
            COLOR_OBJETIVO = captura.getPixel(pixel_x, pixel_y) #rgb

            try:
                muestra_color = captura.crop(pixel_x, pixel_y, w=20, h=20, centered=True)
                b,g,r = muestra_color.meanColor() #ojo devuleve bgr
                COLOR_OBJETIVO = (r,g,b)
                #print COLOR_OBJETIVO
            except Exception as e:
                pass
                print "muestra erronea\n",e

        if FLAG_colorMode_HUE:
            imagen_tratada = captura.hueDistance(COLOR_OBJETIVO).dilate(DILATE).invert().stretch(Umbral_bajo, Umbral_alto)
            imagen_tratada.drawText("HUE" ,20,40,(255,0,255),fontsize=28)
        else:
            imagen_tratada = captura.colorDistance(COLOR_OBJETIVO).dilate(DILATE).invert().stretch(Umbral_bajo, Umbral_alto)
##            imagen_tratada = imagen_tratada.smooth(algorithm_name='gaussian', aperture=(13, 13), sigma=20, spatial_sigma=10, grayscale=False, aperature=None)
            imagen_tratada.drawText("COLOR" ,20,40,(255,0,255),fontsize=28)

        imagen_tratada.morphClose()
        blobs = imagen_tratada.findBlobs()

        if blobs:
            if FLAG_isCircle:
                circulos = blobs.filter([b.isCircle(0.2) for b in blobs])
            else:
                circulos = []
                for b in blobs:
                    if esCirculo(b,toleranciaWH, toleranciaLP, desviacionD):
                        circulos.append(b)
                
            if circulos and circulos[-1].radius()> 10:
                captura.drawCircle((circulos[-1].x, circulos[-1].y), circulos[-1].radius(),Color.BLUE,5)
                imagen_tratada.drawCircle((circulos[-1].x, circulos[-1].y), circulos[-1].radius(),Color.RED,5)
                imagen_tratada.drawText(str(circulos[-1].area()),circulos[-1].x-20, circulos[-1].y-20,(0,0,255),fontsize=18)
                imagen_tratada.drawText(str(circulos[-1].radius()),circulos[-1].x-20, circulos[-1].y+20,(0,0,255),fontsize=18)

        if FLAG_mostrar_tratada:
            imagen_tratada.drawText("Imagen procesada" ,20,20,(255,0,255),fontsize=28)
            imagen_tratada.show()
        else:
            captura.drawText("Normal" ,20,20,(0,255,0),fontsize=28)
            captura.show()   

        if puertoDetectado != None:
            sentido=88  ##con este valor mi servo esta parado
            if (cx < (centro_frame - margen_Centro)):
                sentido = 95 #girar a la derecha
                print"--> girar a la derecha"
            if (cx > (centro_frame + margen_Centro)):
                sentido = 80 #girar a la izquierda
                print"girar a la izquierda <--"
            sendTo_puertoSerie(puertoDetectado, sentido)
         
    display.quit()
