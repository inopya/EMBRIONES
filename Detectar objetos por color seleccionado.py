# -*- coding: utf-8 -*-



## -*- coding: cp1252 -*-

#         _\|/_
#         (O-O)
# -----oOO-(_)-OOo----------------------------------------------------


#######################################################################
# ******************************************************************* #
# *                                                                 * #
# *                   Autor:  Eulogio López Cayuela                 * #
# *                                                                 * #
# *         Utilidad para orientar robot hacia un objeto            * #
#*                      detectado por la camara                     * #
# *                                                                 * #
# *                Version 1.9.0   Fecha: 22/07/2018                * #
# *                                                                 * #
# ******************************************************************* #
#######################################################################

'''
NOTAS:
    - pyton 2.7
    - SimpleCV


Deteccion/Seguimiento de un objeto circular de color determinado.

Usa el BOTON DERECHO sobre la imagen para intercambiar la visualizacion
entre el modo Normal (la captura de la camara) o la Imagen Tratada

Pulsando con el BOTON IZQUIERDO seleccionamos el nuevo color objetivo
El programa trada de encontrar un valor promedio para el color usando la zona adyacente,
de no ser posible se utiliza como color objetivo el del pixel sobre el que se ha pulsado.
 
'''


print __doc__



#--------------------------------------------------------
# IMPORTACION DE MODULOS
#--------------------------------------------------------

#VISION ARTIFICIAL
import SimpleCV
from SimpleCV import Image, Camera, Color, DrawingLayer, Display


#TIEMPOS, FECHAS
import time 
from time import sleep 




#FUNCIONES MATEMATICAS AVANZADAS (matrices...)
import numpy as np






#====================================================================================================
#  INICIO DEL BLOQUE DEFINICION DE VARIABLES GLOBALES y CONSTANTES PARA EL PROGRAMA 
#====================================================================================================


COLOR_OBJETIVO = (255,30,30)

# Parametros para las tolerancias de la funcion esCirculo()
toleranciaWH = 0.15  # 0.15 Tolerancia para mi funcion que localiza los circulos con el 'AspectRadio' del blob
desviacionD = 0.25   # 0.25 desviacion para la funcion interna circleDistance()
toleranciaLP = 0.15  # 0.15 Ratio entre la Longitud del circulo ideal y el perimetro real del blob


resolucion = (320,240)



#algunas variables para el control de las detecciones
DILATE = 1                      #cantidad de dilate ue se aplicara a la imagen (0-xx)
Umbral_Umbral_bajo = 200        #limite inferior y superior para
Umbral_alto = 255               #la aplicacion de  stretch()

FLAG_mostrar_tratada = False    #Si es True muestra la imagen con los filtros aplicados, False muestra la imagen real de la camara (BOTON DERECHO)
FLAG_colorMode_HUE = True       #activar para trabajar en modo HUE, util para evitar los problemas con cambios de iluminacion 
                                #no recomendado lara localizar objetos blancos o negros            

FLAG_isCircle = False           #Si es False se utiliza la funcion interna isCircle(). True se usa la funcion de usuario esCirculo()



FLAG_buscar_circulos = False    #si es True, busca circulos, si es false busca blobs de cualquier forma


#----------------------------------------------------------------------------------------------------
#    FIN DEL BLOQUE DE DEFINICION DE VARIABLES GLOBALES y CONSTANTES PARA EL PROGRAMA 
#----------------------------------------------------------------------------------------------------





#====================================================================================================
# INICIO DEL BLOQUE DE DEFINICION DE FUNCIONES
#====================================================================================================

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






display = Display() #necesario en este caso para poder acceder a metodos relacionados con el raton (posicion y pulsaciones)
webcam = Camera()

while display.isNotDone():

    captura = webcam.getImage().resize(resolucion[0],resolucion[1])

    if display.pressed != None:
        TECLADO = display.pressed[:]
        for indice in range (len(TECLADO)):
            if  TECLADO[indice] == 1:
                print "tecla numero: ", indice
                
    if display.pressed:
        if display.pressed[118]==1: # muestra normal/tratada letra v
            FLAG_mostrar_tratada = not (FLAG_mostrar_tratada)                    
    if display.pressed:
        if display.pressed[104]==1: # mode  huv/color letra h
            FLAG_colorMode_HUE = not (FLAG_colorMode_HUE)
    if display.pressed:
        if display.pressed[98]==1: # blobs/circulos letra b
            FLAG_buscar_circulos = not (FLAG_buscar_circulos)
    if display.pressed:
        if display.pressed[99]==1: #isCircle/escirculo letra c
            FLAG_isCircle = not (FLAG_isCircle)
            
    if display.pressed:
        if display.pressed[273]==1: # dilate tecla flecha arriba
            DILATE+=1
    if display.pressed:
        if display.pressed[274]==1: # dilate tecla flecha abajo 
            if DILATE >0:
                DILATE-=1   

    if display.pressed:
        if display.pressed[275]==1: # aUmbral_bajo tecla flecha derecha 
            if Umbral_bajo <245:
                Umbral_bajo+=10
    if display.pressed:
        if display.pressed[276]==1: # Umbral_bajo tecla flecha izquierda
            if Umbral_bajo >10:
                Umbral_bajo-=10


    if display.mouseRight:
        FLAG_mostrar_tratada = not(FLAG_mostrar_tratada)

    if display.mouseLeft:
        pixel_x, pixel_y = display.mouseRawX, display.mouseRawY 
        COLOR_OBJETIVO = captura.getPixel(pixel_x, pixel_y) #rgb
        #print "pixel_x, pixel_y: ", pixel_x, pixel_y
        print "COLOR_OBJETIVO: ", COLOR_OBJETIVO
        try:
            muestra_color = captura.crop(pixel_x, pixel_y, w=20, h=20, centered=True)
            #muestra_color.show()
            b,g,r = muestra_color.meanColor() #bgr
            COLOR_OBJETIVO = (r,g,b)
        except Exception as e:
            pass


    if FLAG_colorMode_HUE:
        imagen_tratada = captura.hueDistance(COLOR_OBJETIVO).dilate(DILATE).invert().stretch(Umbral_bajo, Umbral_alto)
        #imagen_tratada = imagen_tratada.smooth(algorithm_name='gaussian', aperture=(13, 13), sigma=40, spatial_sigma=0, grayscale=False, aperature=None)
        imagen_tratada.drawText("HUE" ,20,40,(255,0,255),fontsize=28)
    else:
        imagen_tratada = captura.colorDistance(COLOR_OBJETIVO).dilate(DILATE).invert().stretch(Umbral_bajo, Umbral_alto)
        imagen_tratada.drawText("COLOR" ,20,40,(255,0,255),fontsize=28)

    imagen_tratada.morphClose()
    blobs = imagen_tratada.findBlobs()

    if blobs:
        area_objetivo = 0
        circulos = []
        if FLAG_buscar_circulos == True and FLAG_isCircle == True:
            imagen_tratada.drawText("isCircle", 140,20,(255,0,255),fontsize=26)
            circulos = blobs.filter([b.isCircle(0.2) for b in blobs])
            
        if FLAG_buscar_circulos == True and FLAG_isCircle == False:
            imagen_tratada.drawText("esCirculo", 140,20,(255,0,255),fontsize=26)
            circulos = []
            for b in blobs:
                if esCirculo(b,toleranciaWH, toleranciaLP, desviacionD):
                    circulos.append(b)
            
        if circulos and circulos[-1].radius()> 10:
            captura.drawCircle((circulos[-1].x, circulos[-1].y), circulos[-1].radius(),Color.BLUE,5)
            imagen_tratada.drawCircle((circulos[-1].x, circulos[-1].y), circulos[-1].radius(),Color.RED,5)
            imagen_tratada.drawText(str(circulos[-1].area()),circulos[-1].x-20, circulos[-1].y-20,(0,0,255),fontsize=18)

        if FLAG_buscar_circulos == False and blobs[-1].area()> 20:
            imagen_tratada.drawText("blobs", 140,20,(255,0,255),fontsize=26)
            captura.drawCircle((blobs[-1].x, blobs[-1].y), 30,Color.BLUE,5)
            imagen_tratada.drawCircle((blobs[-1].x, blobs[-1].y), 30,Color.RED,5)
            imagen_tratada.drawText(str(blobs[-1].area()),blobs[-1].x-20, blobs[-1].y-20,(0,0,255),fontsize=18)


    if FLAG_mostrar_tratada:
        imagen_tratada.drawText("Procesada", 20,20,(255,0,255),fontsize=28)
        texto = str(DILATE)+" - "+str(Umbral_bajo)
        imagen_tratada.drawText(texto ,120,40,(255,0,255),fontsize=28)
        imagen_tratada.show()
    else:
        captura.drawText("Normal", 20,20,(0,255,0),fontsize=28)
        captura.show()   
     
display.quit()
