import pygame as pg
from math import sqrt
import cv2
from random import randint, uniform
from map_generation import height_map_gen
from PIL import Image
from io import BytesIO
import numpy as np
import cv2
import time

class side_window:
    def __init__(self, menu_num, width, height):
        self.menu_num = menu_num
        self.win_width = width
        self.win_height = height
        self.width = width/7
        self.height = height
        self.pos = (6*self.win_width/7, 0)
        self.corner_pos = (6*self.win_width/7, self.height)
        self.corner_box = (0, self.height-(self.width*self.height)/10000, (self.width*self.height)/10000, (self.width*self.height)/10000)
        self.side_win = pg.Surface((self.width, self.height))
        self.side_win.fill((255,255,255))
        self.side_win.set_alpha(100)
        self.corner_surf = pg.Surface((self.corner_box[2], self.corner_box[3]))
        self.corner_surf.set_alpha(200)
        self.side_win_texts = []
        self.side_win_text_pos = []
        self.side_win_act_text = []
        self.font = pg.font.SysFont("gillsans", 20)

        #Province map
        self.basic_info_pos = (self.pos[0]+10, 10)
        self.basic_info_wh = (abs(self.width-20),abs(self.height/6 - 10))
        self.basic_info_surf = pg.Surface(self.basic_info_wh)
        self.basic_info_surf.set_alpha(200)
        self.basic_text_list = []
        self.basic_c_info_pos = (self.pos[0]+10, 20+self.basic_info_wh[1])
        self.basic_c_info_wh = (abs(self.width-20),abs(self.height/6 - 10))
        self.basic_c_info_surf = pg.Surface(self.basic_c_info_wh)
        self.basic_c_info_surf.set_alpha(200)
        self.basic_c_text_list = []
        self.basic_arc_info_pos = (self.pos[0]+10, 30+self.basic_info_wh[1]+self.basic_c_info_wh[1])
        self.basic_arc_info_wh = (abs(self.width-20),abs(self.height/10 - 10))
        self.basic_arc_info_surf = pg.Surface(self.basic_c_info_wh)
        self.basic_arc_info_surf.set_alpha(200)
        self.basic_arc_text_list = []

        #Heightmap
        self.button_txt = ['Warped Noise Heightmap', 'Plasma Noise Heightmap', 'Grid Province Map', 'Voronoi Province Map', 'Save Maps', 'Make Definitions', 'Make Color Maps', 'Make Terrain Base', 'Get Water Provinces (Slow)', 'The Full Course']
        self.hm = False
        self.hm_wands = False
        self.hm_wh = (abs(self.width-20),abs(self.height/3.5))
        self.hm_pos = (self.pos[0]+10, self.height-self.hm_wh[1]-10)
        self.hm_surf = pg.Surface(self.hm_wh)
        self.hm_surf.fill((255,255,255))
        self.hm_surf.set_alpha(200)
        self.hm_button_txt = ['Fast','Recommended','Islands (Slow)','Archipelago (Slowest)','Fractal (Slow)','Generate',]
        self.hm_wands_txt = ['Flat Circle','Square', 'Bigger', 'Smaller','Reset','Map']
        self.hm_pressed = -1
        self.hm_wands_pressed = -1
        self.hm_wands_radius = 0
        self.rand_gen = [3,randint(4,6),randint(50,500),randint(2,4),round(uniform(0.25,.8),2),2]
        self.hm_gen = height_map_gen(self.win_width, self.win_height)
        self.background = None
        self.show_wand = False
        self.hm_wand = 'Rect'
        self.emap = False

        #Other
        self.pr = False
        self.background = None


    def render(self, win):
        self.update()
        win.blit(self.side_win, (self.corner_pos[0],0))
        win.blit(self.corner_surf, (self.corner_pos[0],self.corner_box[1]))
        if self.menu_num==2 or self.menu_num==3:
            self.draw_basic_prov_txt(win)
            self.draw_basic_c_txt(win)
            self.draw_basic_arc_txt(win)
        
    def draw_height_buttons(self, win, mouse):
        check=self.background
        index = -1
        if self.show_wand and self.hm_wand == 'Circle':
            target_rect = pg.Rect(mouse.get_pos(), (0,0)).inflate((self.hm_wands_radius * 2, self.hm_wands_radius * 2))
            wand_surf = pg.Surface(target_rect.size, pg.SRCALPHA)
            pg.draw.circle(wand_surf, (90,10,10,127), (self.hm_wands_radius, self.hm_wands_radius), self.hm_wands_radius)
            win.blit(wand_surf, target_rect)
        if self.show_wand and self.hm_wand == 'Rect':
            wand_surf = pg.Surface(pg.Rect((mouse.get_pos()[0]-self.hm_wands_radius/2,mouse.get_pos()[1]-self.hm_wands_radius/2,self.hm_wands_radius,self.hm_wands_radius)).size, pg.SRCALPHA)
            pg.draw.rect(wand_surf, (90,10,10,127), wand_surf.get_rect())
            win.blit(wand_surf, pg.Rect(mouse.get_pos()[0]-self.hm_wands_radius/2,mouse.get_pos()[1]-self.hm_wands_radius/2,self.hm_wands_radius,self.hm_wands_radius))
        if self.hm:
            win.blit(self.hm_surf, self.hm_pos)
            for t, button in enumerate(self.hm_button_txt):
                button_txt = self.font.render(f'{button}', 1, (0,0,0))
                pg.draw.rect(win, (255,255,255), (self.hm_pos[0]+10,self.hm_pos[1]+(10*(t+1)+(t*(button_txt.get_height()+5))),self.hm_wh[0]-20, button_txt.get_height()+5))
                win.blit(button_txt, (self.hm_pos[0]+self.hm_wh[0]/2 - button_txt.get_width()/2,self.hm_pos[1]+(10*(t+1)+(t*(button_txt.get_height()+5)))))
                if not self.hm_pressed == t and mouse.get_pressed()[0] and self.hm_pos[0]+10<mouse.get_pos()[0]<self.hm_pos[0]-10+self.hm_wh[0] and self.hm_pos[1]+(10*(t+1)+(t*(button_txt.get_height()+5)))<mouse.get_pos()[1]<self.hm_pos[1]+(10*(t+1)+(t*(button_txt.get_height()+5)))+button_txt.get_height()+5:
                    self.hm_pressed = t
                if mouse.get_pressed()[0]: 
                    if self.hm_pos[0]+10>mouse.get_pos()[0] or mouse.get_pos()[0]>self.hm_pos[0]-10+self.hm_wh[0] or self.hm_pos[1]>mouse.get_pos()[1] or mouse.get_pos()[1]>self.hm_pos[1]+self.hm_wh[1]:
                        self.hm = False
        if self.hm_wands:
            win.blit(self.hm_surf, self.hm_pos)
            for t, button in enumerate(self.hm_wands_txt):
                button_txt = self.font.render(f'{button}', 1, (0,0,0))
                pg.draw.rect(win, (255,255,255), (self.hm_pos[0]+10,self.hm_pos[1]+(10*(t+1)+(t*(button_txt.get_height()+5))),self.hm_wh[0]-20, button_txt.get_height()+5))
                win.blit(button_txt, (self.hm_pos[0]+self.hm_wh[0]/2 - button_txt.get_width()/2,self.hm_pos[1]+(10*(t+1)+(t*(button_txt.get_height()+5)))))
                if not self.hm_wands_pressed == t and mouse.get_pressed()[0] and self.hm_pos[0]+10<mouse.get_pos()[0]<self.hm_pos[0]-10+self.hm_wh[0] and self.hm_pos[1]+(10*(t+1)+(t*(button_txt.get_height()+5)))<mouse.get_pos()[1]<self.hm_pos[1]+(10*(t+1)+(t*(button_txt.get_height()+5)))+button_txt.get_height()+5:
                    self.hm_wands_pressed = t
                elif mouse.get_pressed()[1]:
                   self.hm_wands_pressed = -1
                elif mouse.get_pressed()[0] and self.show_wand:
                    self.background = self.hm_gen.edit_map(self.hm_wand, self.hm_wands_radius, mouse.get_pos(), 1, self.emap)
                elif mouse.get_pressed()[2] and self.show_wand:
                    self.background = self.hm_gen.edit_map(self.hm_wand, self.hm_wands_radius, mouse.get_pos(), -1, self.emap)
        for i, button in enumerate(self.button_txt):
            button_txt = self.font.render(f'{button}', 1, (0,0,0))
            pg.draw.rect(win, (255,255,255), (self.pos[0]+10,self.pos[1]+(10*(i+1)+(i*(button_txt.get_height()+5))),self.width-20, button_txt.get_height()+5))
            win.blit(button_txt, (self.pos[0]+self.width/2 - button_txt.get_width()/2,self.pos[1]+(10*(i+1)+(i*(button_txt.get_height()+5)))))
            if mouse.get_pressed()[0] and self.pos[0]+10<mouse.get_pos()[0]<self.pos[0]-10+self.width and self.pos[1]+(10*(i+1)+(i*(button_txt.get_height()+5)))<mouse.get_pos()[1]<self.pos[1]+(10*(i+1)+(i*(button_txt.get_height()+5)))+button_txt.get_height()+5:
                index = i
                if i==0:
                    self.hm = True
                else:
                    self.hm = False
                if i==1:
                    self.background = self.hm_gen.diamond_square()
                elif i==2:
                    self.background = self.hm_gen.make_province_map()
                    if self.background == None:
                        print('failed')
                if i==3:
                    try:
                        self.background = self.hm_gen.voronoi_province_map()
                    except:
                        self.background = self.hm_gen.voronoi_province_map()
                elif i==4:
                    self.hm_gen.save_maps()
                elif i==5:
                    self.hm_gen.just_def()
                elif i==6:
                    self.background = self.hm_gen.color_maps()
                    if self.background == None:
                        print('failed')
                elif i==7:
                    self.background = self.hm_gen.terrain_base()
                    if self.background == None:
                        print('failed')
                elif i==8:
                    self.hm_gen.get_water_provinces()
                if i==9:
                    self.background = self.hm_gen.full_course()
        if self.hm:
            self.hm_m_log()
        if self.hm_wands:
            self.hm_w_log()

        return index

    def hm_w_log(self):
        b=self.hm_wands_pressed
        if b==2 and self.hm_wands_radius<5000:
            self.hm_wands_radius +=0.5
        if b==3 and self.hm_wands_radius-0.5>0:
            self.hm_wands_radius -=0.5
        if b==4:
            self.hm_gen.edit=self.hm_gen.pic
            self.hm_gen.pedit=self.hm_gen.p_pic
            self.hm_wands_pressed=-1
        if b==5:
            self.emap = not self.emap
            self.hm_wands_pressed=-1


    def hm_m_log(self):
        b=self.hm_pressed
        if not b == -1:
            if b<4:
                self.rand_gen = (b+8)
                self.hm_pressed=-1
            elif b==4: #Fractal
                print('pressed')
                try:
                    self.background = self.hm_gen.fractal(int(5632/4), int(2048/4), uniform(-1.5,1.5), uniform(-2.5,2.5), randint(250,1000), 10**20, randint(0,3))
                except:
                    print('failed')
                    self.background = self.hm_gen.fractal(int(5632/8), int(2048/8), uniform(-1.5,1.5), uniform(-2.5,2.5), randint(250,500), 10**20, randint(0,3))
                self.hm_pressed=-1
            else: #Generate Random Noise
                self.background = self.hm_gen.generate_heightmap(self.rand_gen, randint(200,350),randint(2,3),round(uniform(0.35,.65),2),randint(2,3), randint(2,8))
                self.hm_pressed=-1


    def draw_basic_prov_txt(self, win):
        if self.height>self.basic_info_wh[1]+self.basic_info_pos[1] and self.corner_pos[0]<11*self.win_width/12:
            win.blit(self.basic_info_surf, self.basic_info_pos)
        try:
            for i,txt in enumerate(self.basic_text_list):
                if not i ==None:
                    if i==0 and self.width>self.win_width/10 and self.height>self.basic_info_wh[1]+self.basic_info_pos[1]:
                        text = self.font.render(f'{txt} - {self.basic_text_list[9]}', 1, (255,255,255))
                        win.blit(text, (self.basic_info_pos[0]+self.basic_info_wh[0]/2 -text.get_width()/2 ,self.basic_info_pos[1]))

                    if i==1 and self.width>self.win_width/10 and self.height>self.basic_info_wh[1]+self.basic_info_pos[1]:
                        text = self.font.render(f'Owner: {txt}', 1, (255,255,255))
                        win.blit(text, (self.basic_info_pos[0]+1,self.basic_info_pos[1]+i*text.get_height()))
                    if i==2 and self.width>self.win_width/10 and self.height>self.basic_info_wh[1]+self.basic_info_pos[1]:
                        text = self.font.render(f'Dev: {txt}', 1, (255,255,255))
                        win.blit(text, (self.basic_info_pos[0]+1,self.basic_info_pos[1]+i*text.get_height()))
                    if i==4 and self.width>self.win_width/10 and self.height>self.basic_info_wh[1]+self.basic_info_pos[1]:
                        text = self.font.render(f'Religion: {txt}', 1, (255,255,255))
                        win.blit(text, (self.basic_info_pos[0]+1,self.basic_info_pos[1]+(i-1)*text.get_height()))
                    if i==5 and self.width>self.win_width/10 and self.height>self.basic_info_wh[1]+self.basic_info_pos[1]:
                        text = self.font.render(f'Culture: {txt}', 1, (255,255,255))
                        win.blit(text, (self.basic_info_pos[0]+1,self.basic_info_pos[1]+(i-1)*text.get_height()))
                    if i==8 and self.width>self.win_width/10 and self.height>self.basic_info_wh[1]+self.basic_info_pos[1]:
                        text = self.font.render(f'Trade Good: {txt}', 1, (255,255,255))
                        win.blit(text, (self.basic_info_pos[0]+1,self.basic_info_pos[1]+5*text.get_height()))
        except:
            None

    def draw_basic_c_txt(self, win):
        if self.height>self.basic_c_info_wh[1]+self.basic_c_info_pos[1] and self.corner_pos[0]<11*self.win_width/12:
            win.blit(self.basic_c_info_surf, self.basic_c_info_pos)
        if not self.basic_c_text_list == None:
            for i,txt in enumerate(self.basic_c_text_list):
                if not i ==None:
                    if i==0 and self.width>self.win_width/10 and self.height>self.basic_c_info_wh[1]+self.basic_c_info_pos[1]:
                        text = self.font.render(f'{txt}', 1, (255,255,255))
                        win.blit(text, (self.basic_c_info_pos[0]+self.basic_c_info_wh[0]/2 -text.get_width()/2 ,self.basic_c_info_pos[1]))

                    if i==1 and self.width>self.win_width/10 and self.height>self.basic_c_info_wh[1]+self.basic_c_info_pos[1]:
                        text = self.font.render(f'Gov. Rank: {txt}', 1, (255,255,255))
                        win.blit(text, (self.basic_c_info_pos[0]+1,self.basic_c_info_pos[1]+i*text.get_height()))
                    if i==2 and self.width>self.win_width/10 and self.height>self.basic_c_info_wh[1]+self.basic_c_info_pos[1]:
                        text = self.font.render(f'Religion: {txt}', 1, (255,255,255))
                        win.blit(text, (self.basic_c_info_pos[0]+1,self.basic_c_info_pos[1]+i*text.get_height()))
                    if i==3 and self.width>self.win_width/10 and self.height>self.basic_c_info_wh[1]+self.basic_c_info_pos[1]:
                        text = self.font.render(f'Primary Culture: {txt}', 1, (255,255,255))
                        win.blit(text, (self.basic_c_info_pos[0]+1,self.basic_c_info_pos[1]+i*text.get_height()))
                    if i==4 and self.width>self.win_width/10 and self.height>self.basic_c_info_wh[1]+self.basic_c_info_pos[1]:
                        text = self.font.render(f'Tech. Group: {txt}', 1, (255,255,255))
                        win.blit(text, (self.basic_c_info_pos[0]+1,self.basic_c_info_pos[1]+i*text.get_height()))
                    if i==5 and self.width>self.win_width/10 and self.height>self.basic_c_info_wh[1]+self.basic_c_info_pos[1]:
                        text = self.font.render(f'Mercantalism: {txt}', 1, (255,255,255))
                        win.blit(text, (self.basic_c_info_pos[0]+1,self.basic_c_info_pos[1]+5*text.get_height()))

    def draw_basic_arc_txt(self, win):
        if self.height>self.basic_arc_info_wh[1]+self.basic_arc_info_pos[1] and self.corner_pos[0]<11*self.win_width/12:
            win.blit(self.basic_arc_info_surf, self.basic_arc_info_pos)
        for i,txt in enumerate(self.basic_arc_text_list):
            if not i ==None:
                if i==0 and self.width>self.win_width/10 and self.height>self.basic_arc_info_wh[1]+self.basic_arc_info_pos[1]:
                    text = self.font.render(f'Area: {txt}', 1, (255,255,255))
                    win.blit(text, (self.basic_arc_info_pos[0]+1,self.basic_arc_info_pos[1]+i*text.get_height()))
                if i==1 and self.width>self.win_width/10 and self.height>self.basic_arc_info_wh[1]+self.basic_arc_info_pos[1]:
                    text = self.font.render(f'Region: {txt}', 1, (255,255,255))
                    win.blit(text, (self.basic_arc_info_pos[0]+1,self.basic_arc_info_pos[1]+i*text.get_height()))
                if i==2 and self.width>self.win_width/10 and self.height>self.basic_arc_info_wh[1]+self.basic_arc_info_pos[1]:
                    text = self.font.render(f'Continent: {txt}', 1, (255,255,255))
                    win.blit(text, (self.basic_arc_info_pos[0]+1,self.basic_arc_info_pos[1]+i*text.get_height()))
                if i==3 and self.width>self.win_width/10 and self.height>self.basic_arc_info_wh[1]+self.basic_arc_info_pos[1]:
                    text = self.font.render(f'Trade Node: {txt}', 1, (255,255,255))
                    win.blit(text, (self.basic_arc_info_pos[0]+1,self.basic_arc_info_pos[1]+i*text.get_height()))


    def update(self):
        #Side Bar
        if self.menu_num==2:
            self.width=self.win_width-self.corner_pos[0]
            self.height=self.corner_pos[1]
            self.pos=(self.win_width-self.width, self.height)
        else:
            self.pos=(self.corner_pos[0], 0)
        if sqrt(self.width*self.height)/25>10:
            self.corner_box = (0, self.corner_pos[1]-sqrt(self.width*self.height)/25, sqrt(self.width*self.height)/25, sqrt(self.width*self.height)/25)
        else:
            self.corner_box = (0, self.corner_pos[1]-10, 10, 10)
        self.side_win = pg.transform.scale(self.side_win, (self.width, self.height))
        self.corner_surf = pg.transform.scale(self.corner_surf, (self.corner_box[2], self.corner_box[3]))

        #Basic Info
        self.basic_info_pos = (self.pos[0]+10, 10)
        self.basic_c_info_pos = (self.pos[0]+10, 20+self.basic_info_wh[1])
        self.basic_arc_info_pos = (self.pos[0]+10, 30+self.basic_info_wh[1]+self.basic_c_info_wh[1])
        if self.height>self.win_height/6:
            self.basic_info_wh = (abs(self.width-20),abs(self.win_height/6 - 10))
            self.basic_c_info_wh = (abs(self.width-20),abs(self.win_height/6 - 10))
            self.basic_arc_info_wh = (abs(self.width-20),abs(self.win_height/10 - 10))
        else:
            self.basic_info_wh = (abs(self.width-20),abs(self.height-10))
            self.basic_c_info_wh = (abs(self.width-20),abs(self.height-10))
            self.basic_arc_info_wh = (abs(self.width-20),abs(self.height-10))
        self.basic_info_surf = pg.transform.scale(self.basic_info_surf, self.basic_info_wh)
        self.basic_c_info_surf = pg.transform.scale(self.basic_c_info_surf, self.basic_c_info_wh)
        self.basic_arc_info_surf = pg.transform.scale(self.basic_arc_info_surf, self.basic_arc_info_wh)

        #Height Map
        self.hm_pos = (self.pos[0]+10, self.height-self.hm_wh[1]-10)

        #Other
        if self.width<10 or self.height<10:
            self.side_win.fill((255,255,255))

    def mover(self, new_pos):
        if self.menu_num==2:
            self.corner_pos = (new_pos[0],new_pos[1])
        elif self.menu_num==1 and new_pos[0]<self.win_width-20:
            self.corner_pos = (new_pos[0],self.win_height)

class gui_tools:
    def __init__(self, corner_pos, width, height, province_image, heightmap_image):
        self.win_width = width
        self.win_height = height
        self.corner_pos = corner_pos
        self.area_wh = (self.win_width/6-20,self.win_height/4)
        self.area_pos = [corner_pos[0]+10,corner_pos[1]-10-self.area_wh[1]]
        self.area_surf = pg.Surface(self.area_wh)
        self.area_surf.fill((0,0,0))
        self.area_surf.set_alpha(200)
        self.areas_txt = []
        self.continents_txt = []
        self.trade_node_txt = []
        self.cmd_txt = []
        self.t_set_name = None
        self.a_set_name = None
        self.c_set_name = None
        self.font = pg.font.SysFont("gillsans", 20)
        self.mag_back = pg.Surface((181,181))
        self.mag_back.fill((0,0,0))
        self.mag_back.set_alpha(200)
        self.command = ''
        self.backspace_timer = -1
        self.zoom_level = 0
        self.xmin, self.xmax, self.ymin, self.ymax = 0,self.win_width,0,self.win_height
        self.scroll_amount = []
        self.image = cv2.flip(cv2.rotate(cv2.resize(np.asarray(Image.open(province_image)), (1920,1080), interpolation=cv2.INTER_NEAREST), cv2.ROTATE_90_COUNTERCLOCKWISE), 0)
        self.heightmap = cv2.flip(cv2.rotate(cv2.resize(np.asarray(Image.open(heightmap_image)), (1920,1080), interpolation=cv2.INTER_NEAREST), cv2.ROTATE_90_COUNTERCLOCKWISE), 0)
        self.zoomed_img = self.image

    def commands(self, key, unicode):
        if not key==pg.K_BACKSPACE and not key==pg.K_BACKQUOTE:
            self.command+=unicode
        else:
            if key==pg.K_BACKSPACE:
                self.command = self.command[:-1]
                self.backspace_timer=time.perf_counter()
    
    def draw_cmd_prmt(self, win):
        if round(2*time.perf_counter()) % 2:
            text=self.font.render(self.command+'|', 1, (255,255,255))
        else:
            text=self.font.render(self.command+' ', 1, (255,255,255))
        pg.draw.rect(win, (0,0,0), (5,5,text.get_width(),text.get_height()))
        win.blit(text, (5,5))

    def date_changer(self, win):
        if round(2*time.perf_counter()) % 2:
            text=self.font.render(self.command+'|', 1, (255,255,255))
        else:
            text=self.font.render(self.command+' ', 1, (255,255,255))
        pg.draw.rect(win, (0,0,0), (5,5,text.get_width(),text.get_height()))
        win.blit(text, (5,5))

    def magnifier(self, win, image, mouse_pos):
        try:
            image = self.zoomed_img[mouse_pos[0]-20:mouse_pos[0]+20,mouse_pos[1]-20:mouse_pos[1]+20]
            image = cv2.resize(image, (180,180), interpolation=cv2.INTER_NEAREST)
            zoomed_image = pg.surfarray.make_surface(image)
            win.blit(self.mag_back,(mouse_pos[0]-90, mouse_pos[1]-90))
            win.blit(zoomed_image, (mouse_pos[0]-90, mouse_pos[1]-90))
        except:
            None

    def zoom(self, background):
        self.zoomed_img = self.image
        background = pg.surfarray.make_surface(self.image)
        return background

    def crop(self, start, stop):
        try:
            if np.shape(self.zoomed_img)[2] == 3:
                array = self.zoomed_img
        except:
            array = self.zoomed_img[..., np.newaxis]
            array = np.repeat(array, 3, 2)
        image = np.asarray(array[start[0]:stop[0],start[1]:stop[1]]).astype(np.uint8)
        self.zoomed_img = cv2.resize(image, (self.win_height,self.win_width), interpolation=cv2.INTER_NEAREST)
        scroll = pg.surfarray.make_surface(self.zoomed_img)
        return scroll

    def get_real_cords(self, win, mouse_pos):
        text=self.font.render(f'{round(5632*mouse_pos[0]/1920)}, {round(2048*mouse_pos[1]/1080)}', 1, (255,255,255))
        win.blit(text, mouse_pos)

    def add_arc(self, win, arc):
        if arc==0:
            if self.corner_pos[1]>self.win_height/2 and self.corner_pos[0]<11*self.win_width/12:
                win.blit(self.area_surf, self.area_pos)
                c=0
                d=0
                if self.a_set_name == None:
                    text = self.font.render('Areas:', 1, (255,255,255))
                else:
                    text = self.font.render(f'{self.a_set_name}', 1, (255,255,255))
                win.blit(text, (self.area_pos[0]+self.area_wh[0]/2 -text.get_width()/2 ,self.area_pos[1]))
                if not self.areas_txt == []:
                    for i,txt in enumerate(self.areas_txt):
                            text = self.font.render(f'{txt} ', 1, (255,255,255))
                            if not i % int((self.area_wh[0]-25/(self.win_width-self.area_wh[0]))/60):
                                c+=1
                                d=0
                            win.blit(text, (25+self.area_pos[0]+(d)*(60),self.area_pos[1]+(c+1)*text.get_height()))
                            d+=1
        elif arc==1:
            if self.corner_pos[1]>self.win_height/2:
                win.blit(self.area_surf, self.area_pos)
                c=0
                d=0
                if self.c_set_name == None:
                    text = self.font.render('Continents:', 1, (255,255,255))
                else:
                    text = self.font.render(f'{self.c_set_name}:', 1, (255,255,255))
                win.blit(text, (self.area_pos[0]+self.area_wh[0]/2 -text.get_width()/2 ,self.area_pos[1]))
                if not self.continents_txt == []:
                    for i,txt in enumerate(self.continents_txt):
                            text = self.font.render(f'{txt} ', 1, (255,255,255))
                            if not i % int((self.area_wh[0]-25/(self.win_width-self.area_wh[0]))/60):
                                c+=1
                                d=0
                            win.blit(text, (25+self.area_pos[0]+(d)*(60),self.area_pos[1]+(c+1)*text.get_height()))
                            d+=1
        elif arc==2:
            if self.corner_pos[1]>self.win_height/2:
                win.blit(self.area_surf, self.area_pos)
                c=0
                d=0
                text = self.font.render(f'{self.t_set_name}', 1, (255,255,255))
                win.blit(text, (self.area_pos[0]+self.area_wh[0]/2 -text.get_width()/2 ,self.area_pos[1]))
                if not self.trade_node_txt == []:
                    for i,txt in enumerate(self.trade_node_txt):
                            text = self.font.render(f'{txt} ', 1, (255,255,255))
                            if not i % int((self.area_wh[0]-25/(self.win_width-self.area_wh[0]))/60):
                                c+=1
                                d=0
                            win.blit(text, (25+self.area_pos[0]+(d)*(60),self.area_pos[1]+(c+1)*text.get_height()))
                            d+=1

        elif arc==3:
            if self.corner_pos[1]>self.win_height/2:
                win.blit(self.area_surf, self.area_pos)
                c=0
                d=0
                text = self.font.render('Command Prompt', 1, (255,255,255))
                win.blit(text, (self.area_pos[0]+self.area_wh[0]/2 -text.get_width()/2 ,self.area_pos[1]))
                if not self.cmd_txt == []:
                    for i,txt in enumerate(self.cmd_txt):
                            text = self.font.render(f'{txt} ', 1, (255,255,255))
                            if not i % int((self.area_wh[0]-25/(self.win_width-self.area_wh[0]))/60):
                                c+=1
                                d=0
                            win.blit(text, (25+self.area_pos[0]+(d)*(60),self.area_pos[1]+(c+1)*text.get_height()))
                            d+=1

    def update_areas(self, corner_pos, width, height):
        self.corner_pos = corner_pos
        self.area_wh = (abs(width-20),abs(45+height-self.win_height/2))
        self.area_pos = [corner_pos[0]+10,corner_pos[1]-10-self.area_wh[1]]
        self.area_surf = pg.transform.scale(self.area_surf, self.area_wh)

class m_menu:
    def __init__(self, width, height):
        self.win_width = width
        self.win_height = height
        self.icon_wh = 40
        self.m_width = self.win_width/5
        self.m_height = self.win_height/3
        self.menu_surf = pg.Surface((self.m_width, self.m_height))
        self.menu_surf.fill((245,245,255))
        self.menu_surf.set_alpha(125)
        self.menu_rect = (0,self.win_height-self.icon_wh, self.icon_wh, self.icon_wh)
        self.menu_pos = (self.win_width/2 - self.m_width/2, self.win_height/2 - self.m_height/2)
        self.m_text = ['Map Creation', 'History Editor', 'Map Viewer WNP', 'Exit']
        self.font = pg.font.SysFont("gillsans", 20)
    
    def menu_main(self, win, m_bool, mouse):
        pg.draw.rect(win, (150,255,225), self.menu_rect)
        if m_bool:
            win.blit(self.menu_surf, self.menu_pos)
            for i, button in enumerate(self.m_text):
                button_txt = self.font.render(f'{button}', 1, (0,0,0))
                pg.draw.rect(win, (255,255,255), (self.menu_pos[0]+10,self.menu_pos[1]+(10*(i+1)+(i*(button_txt.get_height()+5))),self.m_width-20, button_txt.get_height()+5))
                win.blit(button_txt, (self.menu_pos[0]+self.m_width/2 - button_txt.get_width()/2,self.menu_pos[1]+(10*(i+1)+(i*(button_txt.get_height()+5)))))
                if mouse.get_pressed()[0] and self.menu_pos[0]+10<mouse.get_pos()[0]<self.menu_pos[0]-10+self.m_width and self.menu_pos[1]+(10*(i+1)+(i*(button_txt.get_height()+5)))<mouse.get_pos()[1]<self.menu_pos[1]+(10*(i+1)+(i*(button_txt.get_height()+5)))+button_txt.get_height()+5:
                    return i+1

class background_setter:
    def __init__(self, width, height):
        self.win_width = width
        self.win_height = height
        self.base_surf = pg.Surface((width, height))
        self.base_surf.fill((50,50,50))
        self.background = self.base_surf
        self.img = self.background

    def converter(self, image):
        with open(image, "rb") as img:
            data = img.read()
        array=np.array(Image.open(BytesIO(data)).convert('RGBA'),copy=False)
        array=cv2.rotate(array, cv2.ROTATE_90_COUNTERCLOCKWISE)
        array=cv2.flip(array, 0)
        picture = pg.Surface(array.shape[0:2], pg.SRCALPHA, 32)
        pg.pixelcopy.array_to_surface(picture, array[:,:,0:3])
        picture_alpha = np.array(picture.get_view('A'), copy=False)
        picture_alpha[:,:] = array[:,:,3]
        return picture

    def get_province_background(self, path):
        return Image.open(path)

class generic_alerts():
    def __init__(self, top_corner=(0,0), size=(0,0), color=(245,245,255), alpha=125, text='', on=False, fade=10, trigger=False): #Fade is in Seconds
        self.top_corner = top_corner
        self.size = size
        self.fade = fade
        self.text = text
        self.on = on
        self.counter=0  #Counts from last time 'on'
        self.Surf = pg.Surface((size[0], size[1]))
        self.Surf.fill(color)
        self.Surf.set_alpha(alpha)
        self.font = pg.font.SysFont("gillsans", 20)
        self.check = -1
        if on:
            self.start = time.perf_counter()

    def update(self, top_corner, size, color=(245,245,255), alpha=125, text='', on=True, fade=10):
        self.top_corner = top_corner
        self.size = size
        self.fade = fade
        self.text = text
        self.on = on
        self.counter=0  #Counts from last time 'on'
        self.Surf = pg.Surface((size[0], size[1]))
        self.Surf.fill(color)
        self.Surf.set_alpha(alpha)
        if on:
            self.start = time.perf_counter()

    def activate(self):
        self.start = time.perf_counter()
        self.counter = 0

    def render(self, win):
        if self.on:
            self.counter=time.perf_counter()
            if not self.counter-self.start>=self.fade:
                win.blit(self.Surf, self.top_corner)
                if '~' in self.text:
                    indexs = [n for n,i in enumerate(self.text) if i == '~']
                    for n,i in enumerate(indexs): 
                        if n>0:
                            button_txt = self.font.render(self.text[indexs[n-1]+1:i], 1, (0,0,0))
                            win.blit(button_txt, (self.top_corner[0]+5,self.top_corner[1]+(n*self.font.get_linesize())))
                        else:
                            button_txt = self.font.render(self.text[0:i], 1, (0,0,0))
                            win.blit(button_txt, (self.top_corner[0]+5,self.top_corner[1]+(n*self.font.get_linesize())))
                    button_txt = self.font.render(self.text[indexs[-1]+1:], 1, (0,0,0))
                    win.blit(button_txt, (self.top_corner[0]+5,self.top_corner[1]+(len(indexs)*self.font.get_linesize())))
                else:
                    button_txt = self.font.render(self.text, 1, (0,0,0))
                    win.blit(button_txt, (self.top_corner[0]+5,self.top_corner[1]))
            else:
                self.on = False
