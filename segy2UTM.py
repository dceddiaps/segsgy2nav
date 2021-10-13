# -*- coding: utf-8 -*-
"""
Created on Fri Jul 24 01:17:49 2020

@author: userDCPS
"""

# Função de filtragem para os dados de nav (filtra erros grosseiros)-----------

def filtragem_nav(coord_x,coord_y):    
    '''
    Filtra em 3 etapas:
        (1) Remove os zeros
        (2) Elimina discrepâncias maiores que 50% do dado (spykes grosseiros)
        (3) Elimina spyke de inversão do dado (Se o dado é positivo, todos
            spykes negativos serão cortados e vice-e-versa)

    Parameters
    ----------
    coord_x : 1Darray
    coord_y : 1Darray

    Returns
    -------
    coord_x : 1Darray
    coord_y : 1Darray

    '''
    
    # Filtragem dos zeros
    zeros = np.unique(np.concatenate((np.where(coord_x == 0)[0], np.where(coord_y == 0)[0])))
    coord_x = np.delete(coord_x, zeros, axis=0)
    coord_y = np.delete(coord_y, zeros, axis=0)
    
    # Filtragem dos valores muito discrepantes (+-50% de discrepância em relação à média)
    discrep_x = np.concatenate((np.where(abs(coord_x) > abs(1.5*coord_x.mean())), np.where(abs(coord_x) < abs(0.5*coord_x.mean()))),axis=1)[0]
    discrep_y = np.concatenate((np.where(abs(coord_y) > abs(1.5*coord_y.mean())), np.where(abs(coord_y) < abs(0.5*coord_y.mean()))),axis=1)[0]
    discrep = np.unique(np.concatenate((discrep_x,discrep_y),axis=0))
    coord_x = np.delete(coord_x, discrep, axis=0)
    coord_y = np.delete(coord_y, discrep, axis=0)
    
    # Filtragem de sinal positivo/negativo
    x_pos = np.where(coord_x > 0)[0]
    y_pos = np.where(coord_y > 0)[0]
    x_neg = np.where(coord_x < 0)[0]
    y_neg = np.where(coord_y < 0)[0]
    
    if str(coord_x.mean())[0] == '-':
        coord_x = np.delete(coord_x, x_pos, axis = 0)
        coord_y = np.delete(coord_y, x_pos, axis = 0)
    if str(coord_y.mean())[0] == '-':
        coord_y = np.delete(coord_y, y_pos, axis = 0)
        coord_x = np.delete(coord_x, y_pos, axis = 0)  
    if str(coord_x.mean())[0] != '-':
        coord_x = np.delete(coord_x, x_neg, axis = 0) 
        coord_y = np.delete(coord_y, x_neg, axis = 0)
    if str(coord_y.mean())[0] != '-':
        coord_y = np.delete(coord_y, y_neg, axis = 0) 
        coord_x = np.delete(coord_x, y_neg, axis = 0) 
    return coord_x,coord_y
    
# Importação de bibliotecas----------------------------------------------------

import glob
import segyio
import numpy as np
from pyproj import Proj
import os
import time

# Importa todos os arquivos de SBP de um diretório-----------------------------

lista = []
extensao = ['*.seg','*.sgy']
for extensao in extensao:   
    root = fr'C:\Users\User W10\any_folder\{extensao}'
    lista.append(glob.glob(root))
lista = lista[0] + lista[1]

# Define a projeção de output das coordenadas----------------------------------
# myProj = Proj("+init=EPSG:32721")
# myProj = Proj("+proj=utm +zone=21 +south +ellps=WGS84 +datum=WGS84 +units=m +epsg:32721")
myProj = Proj("+proj=utm +zone=23 +south +ellps=WGS84 +datum=WGS84 +units=m +epsg:32723")

# Listas para cálculo do máximo e mínimo das coordenadas X/Y-------------------
max_x = []; max_y = []; min_x = []; min_y = []

# Calcula todas as coordenadas XY em UTM para todas as linhas------------------
start = time.time()
for i in range(len(lista)):
    # root_lista = lista[i]
    root_lista = lista[i]
    
    # Esse trecho somente guarda o nome da linha para salvar posteriormente
    f_ = open(fr'{root_lista}','r')
    f_.name
    nome = os.path.basename(f_.name)
    
    # Abre a linha e extrai o atributo desejado
    f = segyio.open(fr'{root_lista}',ignore_geometry=True)
    arcsx = segyio.tools.collect(f.attributes(segyio.TraceField.SourceX))
    arcsy = segyio.tools.collect(f.attributes(segyio.TraceField.SourceY))
    
    arcsx,arcsy = filtragem_nav(arcsx,arcsy)
            
    # Converte arcsecond para decimal degree
    # Engraçado... pesquisei nos bites e não achei justificativa para isso.
    # Imagino que seja uma questão de decimal.
    if root_lista[len(root_lista)-3:len(root_lista):1] == 'seg':
        ddx = arcsx/3600000
        ddy = arcsy/3600000
    if root_lista[len(root_lista)-3:len(root_lista):1] == 'sgy':
        ddx = arcsx/360000
        ddy = arcsy/360000  
    if len(str(abs(int((ddx[0]))))) == 3:
        ddx = ddx/10
        ddy = ddy/10
    
    ddx,ddy = filtragem_nav(ddx,ddy)   
    
    # Converte decimal degree para UTM, no elipsóide especificado
    utmx, utmy = myProj(ddx,ddy) 
    utmx,utmy = filtragem_nav(utmx,utmy)
    res = np.column_stack((utmx,utmy))
    
    max_x.append(utmx.max())
    min_x.append(utmx.min())
    max_y.append(utmy.max())
    min_y.append(utmy.min())
    
    print(f'\nO tamanho da linha {nome} é {np.round(np.linalg.norm(res[0]-res[-1]),3)} metros.')
    
    # Salva arquivo
    #np.savetxt(fr"C:\DCPS\Projetos\Sonar-Sismica 12-09-2017\campo12-09-2017-Sismica\navegação\{nome}_xy.txt",res)

print(f'\nMáximo UTM X = {round(max(max_x),5)}   |   Mínimo UTM X = {round(min(min_x),5)}')
print(f'Máximo UTM Y = {round(max(max_y),5)}  |   Mínimo UTM Y = {round(min(min_y),5)}') 
end = time.time()
print('\nTempo total de operação:',np.round((end-start),8),'segundos\n')    

# plot

# import matplotlib.pyplot as plt
  
# coef = np.polyfit(res[:,0],res[:,1], 1)
# predict = np.poly1d(coef)
# y_lin_reg = predict(res[:,0])
# plt.plot(res[:,0], y_lin_reg, c = 'magenta', label='Lin. reg.',
#          linestyle='dashed')

# x = [res[0,0],res[-1,0]]
# y = [res[0,1],res[-1,1]]
# plt.plot(x,y,c='r',label='Lin. reg. fixig max/min coordinates',
#          linestyle='dashed')

# plt.plot(res[:,0],res[:,1],c='black',label='Data')  

# plt.legend()
# plt.title(f'Line {nome}')
# plt.xlabel('UTM X')
# plt.ylabel('UTM Y')
# plt.grid()
# plt.show()

# print(f'\nO tamanho da linha é de {np.round(np.linalg.norm(res[0]-res[-1]),3)} metros.')









