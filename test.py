# -*- coding: utf-8 -*-
"""
Created on Thu May 24 08:56:07 2018

@author: ic_admin
"""

#Container for display parameters
class DispParms(object):
    def __init__(self):
        self.W = None
        self.H = None

import pygame
import math as m
import numpy as np
import traceback
import csv
import random
from time import time
#import matplotlib.pyplot as plt

pygame.init()

gdisp = DispParms()
gdisp.W = 800
gdisp.H = 600
gameDisplay = pygame.display.set_mode((gdisp.W,gdisp.H))
pygame.display.set_caption('Test Window')

black = (0,0,0)
white = (255,255,255)

car_width = 73

clock = pygame.time.Clock()

bg_grid = pygame.image.load('grid.png')
bg_bridge = pygame.image.load('bridge01.jpg')
bg_bridge_lg = pygame.transform.scale(bg_bridge, (m.floor(800*1.35), m.floor(555*1.35)))
bg_bridge_lgrot = pygame.transform.rotate(bg_bridge_lg, 9)

sprite = pygame.image.load('sprite.png')
sprite_lg = pygame.transform.scale(sprite, (49,84))

sprite_anim = pygame.image.load('sprite-sheet.png')
sprite_anim = pygame.transform.scale(sprite_anim, (sprite_anim.get_width(), sprite_anim.get_height()))

#circle_r = pygame.image.load('circle-r.png')
#circle_rsm = pygame.transform.scale(circle_r, (6, 6))
#circle_rlg = pygame.transform.scale(circle_r, (10, 10))
#circle_b = pygame.image.load('circle-b.png')
#circle_bsm = pygame.transform.scale(circle_b, (6, 6))
#circle_blg = pygame.transform.scale(circle_b, (10, 10))
#
#hextile = pygame.image.load('hex.png')
#hextile_sm = pygame.transform.scale(hextile, (67, 38))
#hexpoint = pygame.image.load('hex2.png')
#hexpoint_sm = pygame.transform.scale(hexpoint, (67, 38))

def gameloop(hexmap='load'):
    
    try:

        gameExit = False
        
        #Define hex grid instance and parameters
        hexg = HexGrid()
        hexg.s = 40 #hex side length
        hexg.aspect = 0.5
        
        #Load or generate hexmap tile properties
        if hexmap=='load':
            with open('bridge_hexmap.csv', 'r') as file:
                reader = csv.reader(file, delimiter=',')
                rowidx = -1
                for row in reader:
                    if rowidx == -1:
                        hexg.griddim = np.array(row).astype(int)
                        hexg.gridpts = np.zeros((hexg.griddim[0], hexg.griddim[1], 3))
                    else:
                        i = m.floor(rowidx/hexg.griddim[1])
                        j = rowidx%hexg.griddim[1]
                        hexg.gridpts[i,j] = np.array(row).astype(float)
                    rowidx += 1
        elif hexmap=='blank':
            hexg.griddim = (m.ceil(gdisp.H/(hexg.s/2)), m.ceil(gdisp.W/(m.sqrt(3)*hexg.s)))
            hexg.gridpts = np.zeros((hexg.griddim[0], hexg.griddim[1], 3))
            for i in range(hexg.gridpts.shape[0]):
                    for j in range(hexg.gridpts.shape[1]):
                        hexg.gridpts[i,j,:] = [0.5*(i*1.5*hexg.s), j*m.sqrt(3)*hexg.s + (i%2)*m.sqrt(3)/2*hexg.s, 1]        
        
        #Place test pawns at start positions
        origin,_ = hexg.nearest_hex(500, 250)
        char1 = Char(gameDisplay, origin, 'Char1')
        origin,_ = hexg.nearest_hex(100, 700)
        char2 = Char(gameDisplay, origin, 'Char2')
        origin,_ = hexg.nearest_hex(100, 600)
        char3 = Char(gameDisplay, origin, 'Char3')
        engmt = Engagement(hexg,[char1, char2, char3])
        
        hexg.engmt = engmt
        
        #initialize pointer mode
        point_mode = 'move'
        
        #Open main game loop
        while not gameExit:
            
            #Draw background
            hexg.render()

            #Check mouse position
            mpos_old = hexg.mpos
            hexg.mpos = pygame.mouse.get_pos()[::-1]
            hexg.mpos = (hexg.mpos[0]-hexg.sc_off[0], hexg.mpos[1]-hexg.sc_off[1])
            minloc, minidx = hexg.nearest_hex(hexg.mpos[0], hexg.mpos[1])
            
            #Draw hexmap
            hexg.hexmap()
            
            #Draw movement range
            if point_mode == 'move': hexg.disp_range()
            else: hexg.tiles = np.empty([0,3])
            
            #Check for input events
            for event in pygame.event.get():
                
                #On EXIT, quit game
                if event.type == pygame.QUIT:
                    gameExit = True
                 
                #On LEFT CLICK (down), start timer
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        hexg.mouse_hold = True
                        t_click = time()
                
                #On LEFT CLICK (release), move char or paint tile
                if event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        hexg.mouse_hold = False
                        t_click = time() - t_click
                        if t_click < 0.2: #If click is short
                            if point_mode == 'move' and np.all(hexg.tiles[:,:2]==minloc, axis=1).any():
                                engmt.activeunit.loc = minloc
                                engmt.next()
                            if point_mode == 'paint:red':
                                hexg.gridpts[minidx[0], minidx[1],2] = 1
                            if point_mode == 'paint:blue':
                                hexg.gridpts[minidx[0], minidx[1],2] = 2
                
                #On SPACEBAR, change pointer mode
                if event.type == pygame.KEYDOWN:
                    if event.key == 32:
                        if point_mode == 'move': point_mode = 'paint:red'
                        elif point_mode == 'paint:red': point_mode = 'paint:blue'
                        elif point_mode == 'paint:blue': point_mode = 'move'
            
            #Draw pointer at nearest hex
            hexg.cursor(minloc[0]+hexg.sc_off[0], minloc[1]+hexg.sc_off[1])
            hexg.pointer(hexg.mpos[0],hexg.mpos[1],point_mode)
        
            #Draw Characters
            #cursor(engmt.activeunit.loc[0], engmt.activeunit.loc[1])
            engmt.render()
        
            pygame.display.update()
            clock.tick(30)
        
            if hexg.mouse_hold:
                mpos_off = (mpos_old[0] - hexg.mpos[0], mpos_old[1] - hexg.mpos[1])
                print("Offset: ", mpos_off)
                if np.linalg.norm(mpos_off) > 0:
                    hexg.sc_off = (hexg.sc_off[0] - mpos_off[0], hexg.sc_off[1] - mpos_off[1])
                    hexg.mpos = (hexg.mpos[0] + mpos_off[0], hexg.mpos[1] + mpos_off[1])
                print("Grdloc: ", hexg.sc_off)
        
        #Save hexmap
        if hexmap=='load':
            with open('bridge_hexmap.csv', 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(hexg.griddim)
                for i in range(hexg.griddim[0]):
                    for j in range(hexg.griddim[1]):
                        writer.writerow(hexg.gridpts[i,j])
            
    except Exception as e:
        traceback.print_exc()
        return e
        
    return 0

class HexGrid:
    
    #Initialize instance attributes
    def __init__(self):
        self.s = None
        self.aspect = None
        self.gridpts = None
        self.griddim = None
        self.engmt = None
        self.sc_off = (0,0)
        self.mouse_hold = False
        self.tiles = None
        self.mpos = None
        
        self.bgfile = 'bridge01.jpg'
        self.bgimg = pygame.image.load('bridge01.jpg')
        self.bgimg = pygame.transform.scale(self.bgimg, (m.floor(800*1.35), m.floor(555*1.35)))
        self.bgimg = pygame.transform.rotate(self.bgimg, 9)
        
        self.hextile = pygame.image.load('hex.png')
        self.hextile = pygame.transform.scale(self.hextile, (67, 38))
        self.hexpoint = pygame.image.load('hex2.png')
        self.hexpoint = pygame.transform.scale(self.hexpoint, (67, 38))

        self.circle_r = pygame.image.load('circle-r.png')
        self.circle_rsm = pygame.transform.scale(self.circle_r, (6, 6))
        self.circle_rlg = pygame.transform.scale(self.circle_r, (10, 10))
        self.circle_b = pygame.image.load('circle-b.png')
        self.circle_bsm = pygame.transform.scale(self.circle_b, (6, 6))
        self.circle_blg = pygame.transform.scale(self.circle_b, (10, 10))
        
    
    #Return all tiles within <dist> tiles of <origin>, ignoring obstacles
    def dist_check(self, dist, origin, blocked = True):
        dy = (self.gridpts[:,:,0] - np.tile(origin[0], self.griddim))*2
        dx = self.gridpts[:,:,1] - np.tile(origin[1], self.griddim)
        
        rgb_dist = np.zeros((3, self.griddim[0], self.griddim[1]))
        rgb_dist[0] = np.round((m.sqrt(3)/3*dx - dy/3)/self.s) #red
        rgb_dist[1] = np.round(-(m.sqrt(3)/3*dx + dy/3)/self.s) #green
        rgb_dist[2] = np.round(2/3*dy/self.s) #blue
        rgb_dist = np.max(np.abs(rgb_dist), axis=0)
        
        tiles = self.gridpts[np.where(rgb_dist == dist)]
        if blocked:
            tiles = tiles[np.where(tiles[:,2]==1)]
            tiles = np.vstack(row for row in tiles if not np.all(self.engmt.loclist==row[:2], 1).any())
        
        return tiles
    
    def hexmap(self):
        for i in range(self.gridpts.shape[0]):
                for j in range(self.gridpts.shape[1]):
                    if self.gridpts[i,j,2] == 1:
                        self.gridmarker(self.gridpts[i,j,0]+self.sc_off[0], self.gridpts[i,j,1]+self.sc_off[1], 'r')
                    elif self.gridpts[i,j,2] == 2:
                        self.gridmarker(self.gridpts[i,j,0]+self.sc_off[0], self.gridpts[i,j,1]+self.sc_off[1], 'b')
    
    #Initialize draw functions
    def hexx(self, y, x):
        gameDisplay.blit(self.hextile, (x-33, y-20))
    def cursor(self, y,x):
        gameDisplay.blit(self.hexpoint, (x-33, y-20))
    def pointer(self, y,x,point_mode):
        if point_mode=='paint:red': gameDisplay.blit(self.circle_rlg, (x-5, y-5))
        if point_mode=='paint:blue': gameDisplay.blit(self.circle_blg, (x-5, y-5))
        
    def gridmarker(self, y, x, color):
        if color=='r': gameDisplay.blit(self.circle_rsm, (x-3, y-3))
        if color=='b': gameDisplay.blit(self.circle_bsm, (x-3, y-3))
    
    #Return all tiles within <dist> tiles of <origin>, avoiding obstacles
    def path_check(self, dist, origin, blocked = True):
        tiles = self.dist_check(1, origin)
        tiles_new = tiles
        for i in range(dist-1):
            tiles_check = tiles_new
            tiles_new = np.empty((0,3))
            for tile in tiles_check:
                tiles_new = np.append(tiles_new, self.dist_check(1, tile[:2]),0)
            tiles = np.append(tiles, tiles_new, 0)
            tiles = tiles[np.where(np.any(tiles[:,:2]!=origin, axis=1))]
        tiles = np.unique(tiles, axis=0)
  
        return tiles
    
    #Find position and index of the hex nearest to the input coordinates
    def nearest_hex(self, y, x):
        dist = np.sqrt(np.square(self.gridpts[:,:,0] - np.tile(y,self.griddim)) + np.square(self.gridpts[:,:,1] - np.tile(x,self.griddim)))
        minidx = np.where(dist==dist.min())
        minidx = (minidx[0][0], minidx[1][0])
        minloc = (self.gridpts[minidx[0],minidx[1],0], self.gridpts[minidx[0],minidx[1],1])
        
        return minloc, minidx
    
    def disp_range(self):
        self.tiles = self.path_check(4, self.engmt.activeunit.loc)
        for tile in self.tiles:
            self.hexx(tile[0]+self.sc_off[0], tile[1]+self.sc_off[1])
        #else:tiles = np.empty([0,3])
    
    def render(self):
        gameDisplay.fill((255,255,255))
        gameDisplay.blit(self.bgimg, (-130+self.sc_off[1],-150+self.sc_off[0]))
        

class Engagement:
    
    def __init__(self, hexg, unitlist):
        self.unitlist = np.array(unitlist)
        self.hexg = hexg
        
        #Check initiatives and activate first character
        self.check_init()
        self.turncount = 0
        self.activeunit = self.unitlist[0]
        print('Active: %s' % self.activeunit.name)
        
        self.check_locs()
    
    #Update and print initiative order
    def check_init(self):
        self.initlist = np.empty([0])
        for unit in self.unitlist:
            self.initlist = np.append(self.initlist, unit.initiative)
        self.unitlist = self.unitlist[np.flipud(np.argsort(self.initlist))]
        print('----------')
        for unit in self.unitlist:
            print('%s: %i' % (unit.name, unit.initiative))
        print('----------')
    
    #Update unit location list
    def check_locs(self):
        self.loclist = np.zeros((0,2))
        for unit in self.unitlist:
            self.loclist = np.append(self.loclist, np.array([unit.loc]), 0)
    
    #Draw all characters
    def render(self):
        self.check_locs()
        self.hexg.cursor(self.activeunit.loc[0]+self.hexg.sc_off[0], self.activeunit.loc[1]+self.hexg.sc_off[1])
        for unit in self.unitlist[np.argsort(self.loclist[:,0])]:
            unit.anim((unit.loc[0]+self.hexg.sc_off[0], unit.loc[1]+self.hexg.sc_off[1]))
            
    def next(self):
        if self.turncount<self.unitlist.size-1:
            self.turncount += 1
        else: self.turncount = 0
        self.activeunit = self.unitlist[self.turncount]
        print('Active: %s' % self.activeunit.name)

class Char:
    
    def __init__(self, disp, loc, name):
        self.name = name
        self.disp = disp
        self.loc = loc
        self.initiative = random.randint(1,21) #Randomize initiative order
        self.frameidx = random.randint(1,15) #Randomize frame offset
        
        self.pawnfile = 'sprite-sheet.png'
        self.pawnsheet = pygame.image.load(self.pawnfile)
        self.pawndims = (self.pawnsheet.get_width()*3, self.pawnsheet.get_height()*3)
        self.pawnsheet = pygame.transform.scale(self.pawnsheet, (self.pawndims[0], self.pawndims[1]))
        self.pawn = pygame.Surface((60, self.pawndims[1]), pygame.SRCALPHA)
        
    def anim(self, loc, action='stand'):
        self.pawn.fill(pygame.Color(0,0,0,0))
        self.pawn.blit(self.pawnsheet, (0,0), (0+60*m.floor(self.frameidx/5),0,self.pawndims[1],self.pawndims[0]))
        self.disp.blit(self.pawn,(loc[1]-25,loc[0]-95))
        
        #Increment or loop frame counter
        if self.frameidx < 14: self.frameidx += 1
        else: self.frameidx = 0


e = gameloop(hexmap='load')
pygame.quit()
#quit()