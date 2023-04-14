from distutils import cmd
import pygame as pg
import numpy as np
from info_grabber import eu4_info
from gui import side_window, gui_tools, m_menu, background_setter, generic_alerts
from map import *
import subprocess
import time
from random import randint, uniform
import io
from PIL import Image
import re
import cv2

def history_editor(menu_num, info):
    #First
    global width
    global height
    width = info.win_width
    height = info.win_height

    #info
    prov_file = None
    info_lock = False

    #pygame
    pg.init()
    #window
    clock = pg.time.Clock()
    win = pg.display.set_mode((width, height))
    window_name=pg.display.set_caption("Modding Overhaul")
    window_name
    background=pg.image.load(info.provinces_file).convert_alpha()
    background=pg.transform.scale(background, (width,height))

    #alt setup
    color_str=''
    open_file = False
    lock_check = False
    open_c_file = False
    map_info = False
    mouse = pg.mouse
    img_set=background_setter(width, height)
    mouse_b = False
    cmd_prmt = False
    date_changer = False
    mid_held = False
    real_chords = False
    
    #gui
    side_win = side_window(menu_num, width, height)
    gui_tool = gui_tools(side_win.corner_pos, width, height, info.provinces_file, info.heightmap_file)
    main_menu = m_menu(width, height)
    move_corner = False
    m_bool = False
    m_e_timer = -1

    #run
    global run
    run = True
    clock = pg.time.Clock()
    while run:
        clock.tick(120)
        win.blit(background, (0,0))
        mouse_pos = mouse.get_pos()
        keys = pg.key.get_pressed()
        events = pg.event.get()
        for event in events: #Events
            if event.type == pg.QUIT:
                pg.quit()
                run = False
                break
            elif event.type == pg.MOUSEWHEEL:
                background = gui_tool.zoom(background)
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_BACKQUOTE: #Command prompt text
                    cmd_prmt = not cmd_prmt
                if not cmd_prmt:
                    if event.key == pg.K_COMMA:
                        date_changer = not date_changer
                    elif  event.key == pg.K_CAPSLOCK:
                        mouse_b = not mouse_b
                    elif event.key == pg.K_PERIOD and not date_changer:
                        real_chords = not real_chords
                if (cmd_prmt or date_changer) and not event.key == pg.K_RETURN:
                    gui_tool.commands(event.key, event.unicode)
                elif cmd_prmt: #Starts Command
                    info.command_prompt(gui_tool.command, gui_tool.cmd_txt)
                elif date_changer:
                    info.date = gui_tool.command.split('.')
            elif event.type == pg.MOUSEBUTTONDOWN:
                if pg.mouse.get_pressed()[0]:
                    if mouse_pos[0]<main_menu.icon_wh and height-main_menu.icon_wh<mouse_pos[1]:
                        m_bool=True
                    elif m_bool and (not main_menu.menu_pos[0]+main_menu.m_width>mouse_pos[0]>main_menu.menu_pos[0] or not main_menu.menu_pos[1]+main_menu.m_height>mouse_pos[1]>main_menu.menu_pos[1]):
                        m_bool = False
                    elif m_bool and main_menu.menu_pos[0]+main_menu.m_width>mouse_pos[0]>main_menu.menu_pos[0] and main_menu.menu_pos[1]+main_menu.m_height>mouse_pos[1]>main_menu.menu_pos[1]:
                        None
                    elif not info_lock and not mouse_b:
                        if side_win.corner_box[0]+side_win.corner_pos[0]<mouse_pos[0]<side_win.corner_box[0]+side_win.corner_box[2]+side_win.corner_pos[0] and side_win.corner_box[1]<mouse_pos[1]<side_win.corner_box[1]+side_win.corner_box[3]:
                            move_corner = True
                        else:
                            color=info.get_color(np.asarray(cv2.resize(cv2.flip(cv2.rotate(pg.surfarray.array3d(background), cv2.ROTATE_90_COUNTERCLOCKWISE), 0), (5632,2048), interpolation=cv2.INTER_NEAREST)), mouse_pos, width, height)
                            color_str=[str(color[0]), str(color[1]), str(color[2])]
                            info.get_country_info(color_str)
                            side_win.basic_text_list=info.prov_info
                            side_win.basic_c_text_list=info.country_info
                            side_win.basic_arc_text_list=info.arc_info
                elif pg.mouse.get_pressed()[2]:
                    if move_corner and mouse_pos[0]<width-10 and mouse_pos[1]>10:
                        move_corner = False

            elif event.type == pg.DROPFILE:
                dropped_path = event.file
                if dropped_path.endswith('provinces.bmp'):
                    info.province_bmp=img_set.get_province_background(dropped_path)
                    background=img_set.converter(dropped_path)
                    background=pg.transform.scale(background, (width, height))
                    info.prov_file_name=dropped_path
                elif dropped_path.endswith('.csv'):
                    try:
                        info.definitions = np.genfromtxt(dropped_path, dtype=str, delimiter=';', skip_header=1, comments='\\',loose=True,filling_values=' ') #Settings
                    except:
                        with io.open(dropped_path, 'r', encoding='UTF-8') as f:
                            lines = [line.encode() for line in f]
                            info.definitions = np.genfromtxt(lines, dtype=str, delimiter=';', skip_header=1, comments='\\',loose=True,filling_values=' ',invalid_raise=False) #Settings
        
        #Key Binds
        if keys[pg.K_LALT] and keys[pg.K_p]:
            info.create_prov_files()
            print('######################')
        if real_chords:
            gui_tool.get_real_cords(win, mouse_pos)
        if pg.mouse.get_pressed()[1] and not mid_held:
            crop_start = mouse_pos
        elif not pg.mouse.get_pressed()[1] and mid_held:
            gui_tool.zoomed_img = gui_tool.image
            try:
                background = gui_tool.crop(crop_start, mouse_pos)
            except:
                None
        if pg.mouse.get_pressed()[1]:
            mid_held = True
        else:
            mid_held = False
        if keys[pg.K_LCTRL]:
            if keys[pg.K_o] and not open_file:
                open_file = True
                prov_file=info.prov_file_name
                if not prov_file==None:
                    prov_file=prov_file.replace('/','\\\\')
                    prov_file=prov_file.replace('\\','\\\\')
                    subprocess.Popen([r'C:\Program Files\Notepad++\notepad++.exe', prov_file])
                    time.sleep(0.5)
            if keys[pg.K_u]:
                info = eu4_info()
                gui_tool.a_set_name=None
                background=pg.image.load(info.provinces_file).convert_alpha()
                background=pg.transform.scale(background, (width,height))
            if keys[pg.K_l] and not lock_check:
                lock_check = True
                info_lock= not info_lock
            if keys[pg.K_c]:
                open_c_file = True
                if not info.country_file_name == None:
                    coun_file=info.country_file_name
                    coun_file=coun_file.replace('/','\\\\')
                    coun_file=coun_file.replace('\\','\\\\')
                    subprocess.Popen([r'C:\Program Files\Notepad++\notepad++.exe', coun_file])
                    time.sleep(0.5)
        if keys[pg.K_m] and not cmd_prmt:
            gui_tool.magnifier(win, info.provinces_file, mouse_pos)
        if keys[pg.K_1]:
            if not map_info:
                map_info = not map_info
                info.get_map_info()
        if mouse_b and pg.mouse.get_pressed()[0]:
            pg.draw.circle(win, (255,0,255), (0,0), 20)
            color=info.get_color(np.asarray(info.province_bmp), mouse_pos, width, height)
            color_str=[str(color[0]), str(color[1]), str(color[2])]
            info.get_country_info(color_str)
            side_win.basic_text_list=info.prov_info
            side_win.basic_c_text_list=info.country_info
            side_win.basic_arc_text_list=info.arc_info


        #Locks
        if not keys[pg.K_o] and keys[pg.K_LCTRL] and open_file:
            open_file = False
        elif not keys[pg.K_l] and keys[pg.K_LCTRL] and lock_check:
            lock_check = False
        elif not keys[pg.K_c] and keys[pg.K_LCTRL] and open_c_file:
            open_c_file = False
        elif not keys[pg.K_1] and map_info:
            map_info = False
        if keys[pg.K_ESCAPE] and 0.5<(time.perf_counter()-m_e_timer):
            m_e_timer = time.perf_counter()
            m_bool = not m_bool
            
        if move_corner:
            side_win.mover(mouse_pos)

        #Render
        side_win.render(win)
        gui_tool.update_areas(side_win.corner_pos,side_win.width,side_win.height)

        # Key Binds
        if cmd_prmt: #Command Prompt
            gui_tool.add_arc(win, 3)
            if pg.mouse.get_pressed()[0]:
                try:
                    if info.prov_info[9] not in gui_tool.cmd_txt and not re.search(f'\W{info.prov_info[9]}\W', f'{info.blocked}'):
                        gui_tool.cmd_txt.append(f'{info.prov_info[9]}')
                except:
                    print('failed to get province info')
            elif pg.mouse.get_pressed()[2]:
                try:
                    gui_tool.cmd_txt.pop(len(gui_tool.cmd_txt)-1)
                    time.sleep(0.1)
                except:
                    gui_tool.cmd_txt=[]
            if keys[pg.K_LCTRL] and keys[pg.K_a]:
                gui_tool.cmd_txt=list(info.definitions[:,0])
        elif keys[pg.K_LALT] and not keys[pg.K_RALT] and not keys[pg.K_LCTRL]: #Areas
            gui_tool.add_arc(win, 0)
            if pg.mouse.get_pressed()[0]:
                if info.prov_info[9] not in gui_tool.areas_txt and not re.search(f'\W{info.prov_info[9]}\W', f'{info.blocked}'):
                    gui_tool.areas_txt.append(f'{info.prov_info[9]}')
            elif pg.mouse.get_pressed()[2]:
                try:
                    gui_tool.areas_txt.pop(len(gui_tool.areas_txt)-1)
                    time.sleep(0.1)
                except:
                    gui_tool.areas_txt=[]
            elif keys[pg.K_a]:
                info.set_acr(gui_tool.areas_txt, 0, gui_tool.a_set_name)
                time.sleep(1)
            elif keys[pg.K_s]:
                if not side_win.basic_arc_text_list == None:
                    gui_tool.a_set_name=side_win.basic_arc_text_list[0]
            elif keys[pg.K_c]:
                gui_tool.a_set_name=None
        elif keys[pg.K_RALT] and not keys[pg.K_LALT]: #Continents
            gui_tool.add_arc(win, 1)
            if pg.mouse.get_pressed()[0]:
                if info.prov_info[9] not in gui_tool.continents_txt and not re.search(f'\W{info.prov_info[9]}\W', f'{info.blocked}'):
                    gui_tool.continents_txt.append(f'{info.prov_info[9]}')
            elif pg.mouse.get_pressed()[2]:
                try:
                    gui_tool.continents_txt.pop(len(gui_tool.continents_txt)-1)
                except:
                    gui_tool.continents_txt=[]
            elif keys[pg.K_a]:
                info.set_acr(gui_tool.continents_txt, 1, gui_tool.c_set_name)
                time.sleep(1)
            elif keys[pg.K_s]:
                if len(side_win.basic_arc_text_list)>0:
                    gui_tool.c_set_name=side_win.basic_arc_text_list[1]
            elif keys[pg.K_c]:
                gui_tool.c_set_name=None
        elif keys[pg.K_LALT] and keys[pg.K_LCTRL] and not keys[pg.K_RALT]: #Trade Nodes
            gui_tool.add_arc(win, 2)
            if pg.mouse.get_pressed()[0]:
                if info.prov_info[9] not in gui_tool.trade_node_txt and not re.search(f'\W{info.prov_info[9]}\W', f'{info.blocked}'):
                    gui_tool.trade_node_txt.append(f'{info.prov_info[9]}')
            elif pg.mouse.get_pressed()[2]:
                try:
                    gui_tool.trade_node_txt.pop(len(gui_tool.trade_node_txt)-1)
                except:
                    gui_tool.trade_node_txt=[]
            elif keys[pg.K_a]:
                info.set_acr(gui_tool.trade_node_txt, 2, gui_tool.t_set_name)
                time.sleep(1)
            elif keys[pg.K_s]:
                if len(side_win.basic_arc_text_list)>2:
                    gui_tool.t_set_name=side_win.basic_arc_text_list[3]
            elif keys[pg.K_c]:
                gui_tool.t_set_name=None
        elif keys[pg.K_RALT] and keys[pg.K_LALT]:
            info.combine_arc()
            time.sleep(1)
        if cmd_prmt:
            gui_tool.draw_cmd_prmt(win)
            if keys[pg.K_BACKSPACE] and time.perf_counter()-gui_tool.backspace_timer>1:
                gui_tool.command = gui_tool.command[:-1]
        if date_changer:
            gui_tool.draw_cmd_prmt(win)
            if keys[pg.K_BACKSPACE] and time.perf_counter()-gui_tool.backspace_timer>1:
                gui_tool.command = gui_tool.command[:-1]


        m_check=main_menu.menu_main(win, m_bool, mouse)
        if not m_check ==None and m_check>0:
            run=False
            break
        m_check=-1
        
        pg.display.flip()
    return m_check

def map_editor(menu_num, info):
    #Start
    global width
    global height
    width = info.win_width
    height = info.win_height

    #info
    prov_file = None
    info_lock = False

    #pygame
    pg.init()
    #window
    clock = pg.time.Clock()
    win = pg.display.set_mode((width, height))
    window_name=pg.display.set_caption("Modding Overhaul")
    window_name
    try:
        background=pg.image.load(info.heightmap_file).convert_alpha()
    except:
        background=pg.image.load('C:\\Program Files (x86)\\Steam\\steamapps\\common\\Europa Universalis IV\\map\\heightmap.bmp').convert_alpha()
    background=pg.transform.scale(background, (width,height))

    #alt setup
    mouse=pg.mouse
    s_check=None
    button_timer=time.perf_counter()
    new_background=None
    img_set=background_setter(width, height)
    mid_held = False
    real_cords = False

    #gui
    side_win = side_window(menu_num, width, height)
    gui_tool = gui_tools(side_win.corner_pos, width, height, info.provinces_file, info.heightmap_file)
    main_menu = m_menu(width, height)
    move_corner = False
    m_bool = False
    m_e_timer = -1
    generic_window=generic_alerts()

    #run
    global run
    run = True
    clock = pg.time.Clock()
    while run:
        clock.tick(120)
        win.blit(background, (0,0))
        mouse_pos=mouse.get_pos()
        keys = pg.key.get_pressed()
        for event in pg.event.get(): #Events
            if event.type == pg.QUIT:
                pg.quit()
                run = False
                break
            if event.type == pg.MOUSEBUTTONDOWN:
                if pg.mouse.get_pressed()[0]:
                    if mouse_pos[0]<main_menu.icon_wh and height-main_menu.icon_wh<mouse_pos[1]:
                        m_bool=True
                    elif m_bool and (not main_menu.menu_pos[0]+main_menu.m_width>mouse_pos[0]>main_menu.menu_pos[0] or not main_menu.menu_pos[1]+main_menu.m_height>mouse_pos[1]>main_menu.menu_pos[1]):
                        m_bool = False
                    elif m_bool and main_menu.menu_pos[0]+main_menu.m_width>mouse_pos[0]>main_menu.menu_pos[0] and main_menu.menu_pos[1]+main_menu.m_height>mouse_pos[1]>main_menu.menu_pos[1]:
                        None
                    if side_win.corner_box[0]+side_win.corner_pos[0]<mouse_pos[0]<side_win.corner_box[0]+side_win.corner_box[2]+side_win.corner_pos[0] and side_win.corner_box[1]<mouse_pos[1]<side_win.corner_box[1]+side_win.corner_box[3]:
                        move_corner = True
                else:
                    if move_corner and mouse_pos[1]>10:
                        move_corner = False
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_PERIOD:
                    real_cords = not real_cords
            if event.type == pg.DROPFILE:
                dropped_path = event.file
                if dropped_path.endswith('heightmap.bmp'):
                    info.heightmap_bmp=img_set.get_province_background(dropped_path)
                    background=img_set.converter(dropped_path)
                    background=pg.transform.scale(background, (width, height))
                    info.heightmap_file=dropped_path
                    side_win.hm_gen.pic=np.array(Image.open(dropped_path))
                    side_win.hm_gen.p_pic=np.array(Image.open(dropped_path))

        if keys[pg.K_ESCAPE] and 1<(time.perf_counter()-m_e_timer):
            m_e_timer = time.perf_counter()
            m_bool = not m_bool

        if keys[pg.K_p]:
            background=side_win.hm_gen.array_to_bkgrnd(side_win.hm_gen.p_pic)

        if keys[pg.K_h]:
            background=side_win.hm_gen.array_to_bkgrnd(side_win.hm_gen.pic)
            
        if keys[pg.K_m]:
            gui_tool.magnifier(win, info.heightmap_file, mouse_pos)

        if pg.mouse.get_pressed()[1] and not mid_held:
            crop_start = mouse_pos
        elif not pg.mouse.get_pressed()[1] and mid_held:
            gui_tool.zoomed_img = gui_tool.heightmap
            try:
                background = gui_tool.crop(crop_start, mouse_pos)
            except:
                None
        if pg.mouse.get_pressed()[1]:
            mid_held = True
        else:
            mid_held = False

        if real_cords:
            gui_tool.get_real_cords(win, mouse_pos)

        if move_corner:
            side_win.mover(mouse_pos)
        
        #Render
        side_win.render(win)
        hm_button_pressed=side_win.draw_height_buttons(win, mouse)
        if hm_button_pressed>=0:
            if hm_button_pressed==6:
                generic_window.update((width/2 - width/10,height/2 - height/10), size=(width/5,height/5), text='My machine learning model can make a~realistic one - just DM me!~~This just generates something for you to~base something off of')
            if hm_button_pressed==8:
                generic_window.update((width/2 - width/10,height/2 - height/10), size=(width/5,height/5), text='This checks the definitions file in your mod!~~If you do not have one yet, generate one~then paste it after the file header')               
            hm_button_pressed=-1
        new_background=side_win.background
        generic_window.render(win)
        
        if not new_background == None:
            background = new_background
            side_win.background = None

        m_check=main_menu.menu_main(win, m_bool, mouse)
        if not m_check ==None and m_check>0:
            run=False
            break
        m_check=-1
        
        pg.display.flip()
    return m_check

def map_viewer(menu_num, info): #Currently Broken
    return 4
    #First
    global width
    global height
    width = info.win_width
    height = info.win_height

    #pygame
    pg.init()
    #window
    clock = pg.time.Clock()
    win = pg.display.set_mode((width, height))
    window_name=pg.display.set_caption("Modding Overhaul")
    window_name
    background=pg.image.load(info.provinces_file).convert_alpha()
    background=pg.transform.scale(background, (width,height))

    #alt setup
    color_str=''
    open_file = False
    lock_check = False
    open_c_file = False
    map_info = False
    mouse = pg.mouse
    img_set=background_setter(width, height)
    mouse_b = False
    cmd_prmt= False
    
    #gui
    side_win = side_window(menu_num, width, height)
    gui_tool = gui_tools(side_win.corner_pos, width, height, info.provinces_file, info.heightmap_file)
    main_menu = m_menu(width, height)
    move_corner = False
    m_bool = False
    m_e_timer = -1

    #info
    now=time.perf_counter()
    Provinces = collect_provinces(np.asarray(info.province_bmp), info.definitions[:,1:4], info)
    prov_file = None
    info_lock = False
    data=False


    #run
    global run
    run = True
    clock = pg.time.Clock()
    while run:
        clock.tick(120)
        win.blit(background, (0,0))
        mouse_pos = mouse.get_pos()
        keys = pg.key.get_pressed()
        events = pg.event.get()
        for event in events: #Events
            if event.type == pg.QUIT:
                pg.quit()
                run = False
                break
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_CAPSLOCK:
                    mouse_b = not mouse_b
            if event.type == pg.MOUSEBUTTONDOWN:
                if pg.mouse.get_pressed()[0]:
                    if mouse_pos[0]<main_menu.icon_wh and height-main_menu.icon_wh<mouse_pos[1]:
                        m_bool=True
                    elif m_bool and (not main_menu.menu_pos[0]+main_menu.m_width>mouse_pos[0]>main_menu.menu_pos[0] or not main_menu.menu_pos[1]+main_menu.m_height>mouse_pos[1]>main_menu.menu_pos[1]):
                        m_bool = False
                    elif m_bool and main_menu.menu_pos[0]+main_menu.m_width>mouse_pos[0]>main_menu.menu_pos[0] and main_menu.menu_pos[1]+main_menu.m_height>mouse_pos[1]>main_menu.menu_pos[1]:
                        None
                    elif not info_lock and not mouse_b:
                        if side_win.corner_box[0]+side_win.corner_pos[0]<mouse_pos[0]<side_win.corner_box[0]+side_win.corner_box[2]+side_win.corner_pos[0] and side_win.corner_box[1]<mouse_pos[1]<side_win.corner_box[1]+side_win.corner_box[3]:
                            move_corner = True
                        else:
                            color=info.get_color(np.asarray(info.province_bmp), mouse_pos, width, height)
                            color_str=[str(color[0]), str(color[1]), str(color[2])]
                            info.get_country_info(color_str)
                            side_win.basic_text_list=info.prov_info
                            side_win.basic_c_text_list=info.country_info
                            side_win.basic_arc_text_list=info.arc_info
                else:
                    if move_corner and mouse_pos[0]<width-10 and mouse_pos[1]>10:
                        move_corner = False
            if event.type == pg.DROPFILE:
                dropped_path = event.file
                if dropped_path.endswith('provinces.bmp'):
                    info.province_bmp=img_set.get_province_background(dropped_path)
                    background=img_set.converter(dropped_path)
                    background=pg.transform.scale(background, (width, height))
                    info.prov_file_name=dropped_path
                elif dropped_path.endswith('.csv'):
                    try:
                        info.definitions = np.genfromtxt(dropped_path, dtype=str, delimiter=';', skip_header=1, comments='\\',loose=True,filling_values=' ') #Settings
                    except:
                        with io.open(dropped_path, 'r', encoding='UTF-8') as f:
                            lines = [line.encode() for line in f]
                            info.definitions = np.genfromtxt(lines, dtype=str, delimiter=';', skip_header=1, comments='\\',loose=True,filling_values=' ',invalid_raise=False) #Settings
        #Map
        if not data:
            info_time = time.perf_counter()
            print(time.perf_counter()-info_time, 'start provinces')
            for i, prov in enumerate(Provinces):
                set_province_info(info, prov)
                if not i % 10:
                    print(time.perf_counter()-info_time, i)
            print(time.perf_counter()-info_time, 'finish provinces', Provinces[0].p_data)
            data = not data

        if keys[pg.K_1]: #Development
            dev_time = time.perf_counter()
            print(time.perf_counter()-dev_time, 'dev')
            for province in Provinces[:1000]:
                if not province.data == [[],[],[]]:
                    print('worked', province.data)
                else:
                    print(province.id, province.data)
                pg.event.pump()
            print(time.perf_counter()-dev_time, 'dev')

        
        #Shortcuts
        if keys[pg.K_ESCAPE] and 1<(time.perf_counter()-m_e_timer):
            m_e_timer = time.perf_counter()
            m_bool = not m_bool
        if keys[pg.K_LCTRL]:
            if keys[pg.K_o] and not open_file:
                open_file = True
                prov_file=info.prov_file_name
                if not prov_file==None:
                    prov_file=prov_file.replace('/','\\\\')
                    prov_file=prov_file.replace('\\','\\\\')
                    subprocess.Popen([r'C:\Program Files\Notepad++\notepad++.exe', prov_file])
                    time.sleep(0.5)
            if keys[pg.K_u]:
                info = eu4_info()
                gui_tool.a_set_name=None
                background=pg.image.load(info.provinces_file).convert_alpha()
                background=pg.transform.scale(background, (width,height))
            if keys[pg.K_l] and not lock_check:
                lock_check = True
                info_lock= not info_lock
            if keys[pg.K_c]:
                open_c_file = True
                if not info.country_file_name == None:
                    coun_file=info.country_file_name
                    coun_file=coun_file.replace('/','\\\\')
                    coun_file=coun_file.replace('\\','\\\\')
                    subprocess.Popen([r'C:\Program Files\Notepad++\notepad++.exe', coun_file])
                    time.sleep(0.5)
        if keys[pg.K_m] and not cmd_prmt:
            gui_tool.magnifier(win, info.provinces_file, mouse_pos)
        if keys[pg.K_1]:
            if not map_info:
                map_info = not map_info
                info.get_map_info()
        if mouse_b and pg.mouse.get_pressed()[0]:
            pg.draw.circle(win, (255,0,255), (0,0), 20)
            color=info.get_color(np.asarray(info.province_bmp), mouse_pos, width, height)
            color_str=[str(color[0]), str(color[1]), str(color[2])]
            info.get_country_info(color_str)
            side_win.basic_text_list=info.prov_info
            side_win.basic_c_text_list=info.country_info
            side_win.basic_arc_text_list=info.arc_info

        #Locks
        if not keys[pg.K_o] and keys[pg.K_LCTRL] and open_file:
            open_file = False
        elif not keys[pg.K_l] and keys[pg.K_LCTRL] and lock_check:
            lock_check = False
        elif not keys[pg.K_c] and keys[pg.K_LCTRL] and open_c_file:
            open_c_file = False
        elif not keys[pg.K_1] and map_info:
            map_info = False
            
        if move_corner:
            side_win.mover(mouse_pos)

        #Render
        side_win.render(win)
        gui_tool.update_areas(side_win.corner_pos,side_win.width,side_win.height)

        #Key Binds
        if keys[pg.K_LALT] and not keys[pg.K_RALT] and not keys[pg.K_LCTRL]: #Areas
            gui_tool.add_arc(win, 0)
            if pg.mouse.get_pressed()[0]:
                if info.prov_info[9] not in gui_tool.areas_txt and not re.search(f'\W{info.prov_info[9]}\W', f'{info.blocked}'):
                    gui_tool.areas_txt.append(f'{info.prov_info[9]}')
            elif pg.mouse.get_pressed()[2]:
                try:
                    gui_tool.areas_txt.pop(len(gui_tool.areas_txt)-1)
                    time.sleep(0.1)
                except:
                    gui_tool.areas_txt=[]
            elif keys[pg.K_a]:
                info.set_acr(gui_tool.areas_txt, 0, gui_tool.a_set_name)
                time.sleep(1)
            elif keys[pg.K_s]:
                if not side_win.basic_arc_text_list == None:
                    gui_tool.a_set_name=side_win.basic_arc_text_list[0]
            elif keys[pg.K_c]:
                gui_tool.a_set_name=None
        elif keys[pg.K_RALT] and not keys[pg.K_LALT]: #Continents
            gui_tool.add_arc(win, 1)
            if pg.mouse.get_pressed()[0]:
                if info.prov_info[9] not in gui_tool.continents_txt and not re.search(f'\W{info.prov_info[9]}\W', f'{info.blocked}'):
                    gui_tool.continents_txt.append(f'{info.prov_info[9]}')
            elif pg.mouse.get_pressed()[2]:
                try:
                    gui_tool.continents_txt.pop(len(gui_tool.continents_txt)-1)
                except:
                    gui_tool.continents_txt=[]
            elif keys[pg.K_a]:
                info.set_acr(gui_tool.continents_txt, 1, gui_tool.c_set_name)
                time.sleep(1)
            elif keys[pg.K_s]:
                if len(side_win.basic_arc_text_list)>0:
                    gui_tool.c_set_name=side_win.basic_arc_text_list[1]
            elif keys[pg.K_c]:
                gui_tool.c_set_name=None
        elif keys[pg.K_LALT] and keys[pg.K_LCTRL] and not keys[pg.K_RALT]: #Trade Nodes
            gui_tool.add_arc(win, 2)
            if pg.mouse.get_pressed()[0]:
                if info.prov_info[9] not in gui_tool.trade_node_txt and not re.search(f'\W{info.prov_info[9]}\W', f'{info.blocked}'):
                    gui_tool.trade_node_txt.append(f'{info.prov_info[9]}')
            elif pg.mouse.get_pressed()[2]:
                try:
                    gui_tool.trade_node_txt.pop(len(gui_tool.trade_node_txt)-1)
                except:
                    gui_tool.trade_node_txt=[]
            elif keys[pg.K_a]:
                info.set_acr(gui_tool.trade_node_txt, 2, gui_tool.t_set_name)
                time.sleep(1)
            elif keys[pg.K_s]:
                if len(side_win.basic_arc_text_list)>2:
                    gui_tool.t_set_name=side_win.basic_arc_text_list[3]
            elif keys[pg.K_c]:
                gui_tool.t_set_name=None
        elif keys[pg.K_RALT] and keys[pg.K_LALT]:
            info.combine_arc()
            time.sleep(1)
        if cmd_prmt:
            gui_tool.draw_cmd_prmt(win)
            if keys[pg.K_BACKSPACE] and time.perf_counter()-gui_tool.backspace_timer>1:
                gui_tool.command = gui_tool.command[:-1]

        if keys[pg.K_p]:
            save_provinces(Provinces)
        m_check=main_menu.menu_main(win, m_bool, mouse)
        if (not m_check == None and m_check>0):
            save_provinces(Provinces)
            run=False
            break
        m_check=-1
        
        pg.display.flip()
    return m_check