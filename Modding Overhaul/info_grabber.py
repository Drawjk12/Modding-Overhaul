import numpy as np
from PIL import Image
from glob import glob
import re
import cv2
import os
import string
from random import choice
import io

class eu4_info:
    def __init__(self):
        self.start_path=os.path.split(os.path.dirname(__file__))[0]
        self.start_path=self.start_path.replace('\\','/')
        self.start_path=self.start_path.replace('//','/')
        self.settings=np.genfromtxt(self.start_path + '/Modding Overhaul/SETTINGS.txt', skip_header=4, dtype='str',delimiter=';')
        try:
            np.array(Image.open(self.settings[0]+'map/provinces.bmp'))
            self.provinces_file = self.settings[0]+'map/provinces.bmp'
        except:
            self.provinces_file = 'C:\\Program Files (x86)\\Steam\\steamapps\\common\\Europa Universalis IV\\map\\provinces.bmp'
        try:
            self.heightmap_file = self.settings[0]+'map/heightmap.bmp'
            np.array(Image.open(self.heightmap_file))
        except:
            self.heightmap_file = 'C:\\Program Files (x86)\\Steam\\steamapps\\common\\Europa Universalis IV\\map\\heightmap.bmp'
        self.defines_file = self.settings[0]+r'map\definition.csv'
        try:
            self.province_bmp = Image.open(self.provinces_file)
        except:
            self.province_bmp = Image.open('C:\\Program Files (x86)\\Steam\\steamapps\\common\\Europa Universalis IV\\map\\provinces.bmp')
            self.defines_file = 'C:\\Program Files (x86)\\Steam\\steamapps\\common\\Europa Universalis IV\\map\\definition.csv'
        try:
            self.heightmap_bmp = Image.open(self.heightmap_file)
        except:
            self.province_bmp = Image.open('C:\\Program Files (x86)\\Steam\\steamapps\\common\\Europa Universalis IV\\map\\heightmap.bmp')
        try:
            self.blocked=open(self.settings[0]+'blocked.txt').readlines()
        except:
            self.blocked=['']
        try:
            self.definitions = np.genfromtxt(self.settings[0]+r'map\definition.csv', dtype=str, delimiter=';', skip_header=1, comments='\\',loose=True,filling_values=' ') #Settings
        except:
            try:
                with io.open(self.defines_file, encoding='ANSI') as f:
                    lines = [line.encode() for line in f]
                    self.definitions = np.genfromtxt(lines, dtype=str, delimiter=';', skip_header=1, comments='\\',loose=True,filling_values=' ',invalid_raise=False) #Settings
            except:
                try:
                    self.definitions = np.genfromtxt(r'C:\Program Files (x86)\Steam\steamapps\common\Europa Universalis IV/'+r'map\definition.csv', dtype=str, delimiter=';', skip_header=1, comments='\\',loose=True,filling_values=' ')
                except:
                    self.definionts = []
        self.win_width = int(self.settings[2].split(',')[0])
        self.win_height = int(self.settings[2].split(',')[1])
        try:
            self.date = self.settings[1].split('.')
        except:
            print('failed')
            self.date = [1444,11,11]
        self.prov_info = None
        self.prov_file_name = None
        self.country_info = None
        self.country_file_name = None
        self.arc_info = None
        self.arc_weird_bool=True
        self.ids = []

    def get_color(self, image, pos, width, height):
        og_image = image
        image = cv2.resize(image, dsize=(width, height), interpolation=cv2.INTER_NEAREST )
        return image[pos[1]][pos[0]]

    def get_country_info(self, color_str):
        id = self.get_province_id(color_str)
        self.get_province_info(id)
        try:
            self.find_country_info(self.prov_info[1])
        except:
            None
        self.get_region_info(id)

    def get_province_id(self, color_str):
        id = (self.definitions[:,1]==color_str[0]) & (self.definitions[:,2]==color_str[1]) & (self.definitions[:,3]==color_str[2])
        return str(id.nonzero()[0][0])

    def get_province_info(self, id):
        owner = None
        prov_name = None
        base_tax, base_production, base_manpower = None, None, None
        dev, dev_tot = None, None
        religion, culture = None, None
        center_of_trade, hre, trade_goods = None, None, None
        province_file_names = glob(self.settings[0]+r'history\provinces'+'\*.txt') #Settings
        name = None
        list_count = 0
        for name in province_file_names:
            real_name = name.replace(self.settings[0]+r'history\provinces'+'\\', '') #Settings
            if id==real_name[:len(id)]:
                prov_name = real_name.replace(f'{id}', '')
                prov_name = prov_name.replace(f'-', '')
                prov_name = prov_name.replace('.txt', '')
            else:
                prov_name = 'Unknown'
                list_count+=1

            match_one = re.search(f'^{id}-', real_name)
            match_two = re.search(f'^{id} -', real_name)
            match_three = re.search(f'^{id}.txt', real_name)

            if match_one or match_two or match_three:
                break
        if len(province_file_names)<=list_count:
            self.create_prov_files()
            self.country_info = None
            return None
        try:
            with open(name, buffering=(2<<16) + 8) as prov:
                prov_lines = prov.readlines()
        except:
            Exception(f'Failed to find path {name}')
        check_lines = []
        checker = False
        for line in prov_lines:
            if len(line)<1:
                continue
            try:
                if re.search('\d{1,99}\.\d{1,2}\.\d{1,2}', line):
                    d1 = int(re.findall('^(\d{1,99})', line)[0])
                    d2 = int(re.findall('\.(\d{1,2})\.', line)[0])
                    d3 = int(re.findall('\.(\d{1,2}) ', line)[0])
                    if d1<int(self.date[0]):
                        line = line.replace('.', '')
                        line = line.replace(str(d1), '')
                        line = line.replace(str(d2), '')
                        line = line.replace(str(d3), '')
                        line = line.replace(' = { ', '')
                        line = line.replace(' }', '')
                        checker = True
                    elif d1==int(self.date[0]) and int(d2<self.date[1]):
                        line = line.replace('.', '')
                        line = line.replace(str(d1), '')
                        line = line.replace(str(d2), '')
                        line = line.replace(str(d3), '')
                        line = line.replace(' = { ', '')
                        line = line.replace(' }', '')
                        checker = True
                    elif d1==int(self.date[0]) and int(d2==self.date[1]) and int(d3<self.date[2]):
                        line = line.replace('.', '')
                        line = line.replace(str(d1), '')
                        line = line.replace(str(d2), '')
                        line = line.replace(str(d3), '')
                        line = line.replace(' = { ', '')
                        line = line.replace(' }', '')
                        checker = True
                    else:
                        checker = False
                if checker:
                    if re.search('\t', line):
                        line = line.replace('\t','')
                    for new_line in re.findall('\w{1,99} = \w{1,99}', line):
                        check_lines.append(new_line)
                else:
                    check_lines.append(line)
            except:
                check_lines.append(line)

        for line in check_lines:
            if len(line)<1:
                continue
            if not re.search('{',line):
                line = re.sub('#.*','', line)

                if re.search('^owner = \w{3}', line):
                    owner = line.replace('owner = ', '')
                    owner = owner.replace('\n', '')[:3]
                if re.search('^base_tax = \d', line):
                    base_tax = line.replace('base_tax = ', '')
                    base_tax = base_tax.replace('\n', '')
                if re.search('^base_production = \d', line):
                    base_production = line.replace('base_production = ', '')
                    base_production = base_production.replace('\n', '')
                if re.search('^base_manpower = \d', line):
                    base_manpower = line.replace('base_manpower = ', '')
                    base_manpower = base_manpower.replace('\n', '')
                if not base_tax == None and not base_production == None and not base_manpower == None:
                    dev = [base_tax, base_production, base_manpower]
                    try:
                        dev_tot = str(eval(f'{base_tax}+{base_production}+{base_manpower}'))
                    except:
                        None
                    if not len(dev)==3:
                        dev = ['Error', 'Error', 'Error']

                if re.search('^culture = \w{1,99}', line):
                    culture = line.replace('culture = ', '')
                    culture = culture.replace('\n', '')
                if re.search('^religion = \w{1,99}', line):
                    religion = line.replace('religion = ', '')
                    religion = religion.replace('\n', '')

                if re.search('^center_of_trade = \d', line):
                    center_of_trade = line.replace('center_of_trade = ', '')
                    center_of_trade = center_of_trade.replace('\n', '')
                if re.search('^hre = \w{1,3}', line):
                    hre = line.replace('hre = ', '')
                    hre = hre.replace('\n', '')
                if re.search('^trade_goods = \w{1,99}', line):
                    trade_goods = line.replace('trade_goods = ', '')
                    trade_goods = trade_goods.replace('\n', '')

        self.prov_file_name = name
        self.prov_info = [prov_name, owner, dev, dev_tot, religion, culture, center_of_trade, hre, trade_goods, id]
        return self.prov_info

    def find_country_info(self, owner):
        self.country_info = []
        government, gov_rank = None, None
        religion, primary_culture = None, None
        tech_group, mercantilism = None, None
        country_files = glob(self.settings[0]+r'history\countries'+'\*.txt') #Settings
        country_file = None
        for country in country_files:
            if re.search(f'{owner}', country):
                country_file = country
                break
        self.country_file_name = country_file
        country_txt = []
        if not country_file == None:
            with open(country_file) as cntry:
                country_txt = cntry.readlines()
                cntry.close()
            for line in country_txt:
                if re.search('^government = \w{1,99}', line):
                    government = line.replace('government = ', '')
                    government = government.replace('\W', '')
                    government = government.replace('\n', '')
                if re.search('^government_rank = \d', line):
                    gov_rank = line.replace('government_rank = ', '')
                    gov_rank = gov_rank.replace('\n', '')

                if re.search('^religion = \w{1,99}', line):
                    religion = line.replace('religion = ', '')
                    religion = religion.replace('\n', '')
                if re.search('^primary_culture = \w{1,99}', line):
                    primary_culture = line.replace('primary_culture = ', '')
                    primary_culture = primary_culture.replace('\n', '')

                if re.search('^technology_group = \w{1,99}', line):
                    tech_group = line.replace('technology_group = ', '')
                    tech_group = tech_group.replace('\n', '')
                if re.search('^mercantilism = \d{1,4}', line):
                    mercantilism = line.replace('mercantilism = ', '')
                    mercantilism = mercantilism.replace('\n', '')

            self.country_info = [government, gov_rank, religion, primary_culture, tech_group, mercantilism]
        else:
            return Exception('Couldn\'t Retrieve Country Info')

    def get_region_info(self, id):
        area = None
        region = None
        continent = None
        trade_node = None

        #Area
        area_lines = []
        try:
            with open(self.settings[0]+r'map\area.txt', 'r') as areas: #Settings
                area_lines = areas.readlines()
                areas.close()
        except:
            self.arc_weird_bool=not self.arc_weird_bool
            self.combine_arc()
            with open(self.settings[0]+r'map\area.txt', 'r') as areas: #Settings
                area_lines = areas.readlines()
                areas.close()
        for i,line in enumerate(area_lines):
            if re.search(f'\D{id}\D', line):
                loop=True
                counter=0
                try:
                    while loop:
                        if re.search('{', area_lines[i+counter]) and not re.search('color', area_lines[i+counter]):
                            area=area_lines[i+counter]
                            loop=False
                        counter-=1
                except:
                    return Exception('failed to get continent')
        if not area == None:
            area = re.sub('#.*','', area)
            area = re.sub('\W','', area)
            area = re.sub('\d','', area)

        #Region
        region_lines = []
        with open(self.settings[0]+r'map\region.txt', 'r') as regions: #Settings
            region_lines = regions.readlines()
            regions.close()
        for i,line in enumerate(region_lines):
            if re.search(f'{area}', line):
                loop=True
                counter=0
                try:
                    while loop:
                        if re.search('{', region_lines[i+counter]) and not re.search('areas', region_lines[i+counter]):
                            region=region_lines[i+counter]
                            loop=False
                        counter-=1
                except:
                    return Exception('failed to get continent')
        if not region == None:
            region = re.sub('#.*','', region)
            region = re.sub('\W','', region)
            region = re.sub('\d','', region)

        #Continent
        continent_lines = []
        with open(self.settings[0]+r'map\continent.txt', 'r') as continents: #Settings
            continent_lines = continents.readlines()
            continents.close()
        for i,line in enumerate(continent_lines):
            if re.search(f'\D{id}\D', line):
                loop=True
                counter=0
                try:
                    while loop:
                        if re.search('{', continent_lines[i+counter]):
                            continent=continent_lines[i+counter]
                            loop=False
                        counter-=1
                except:
                    return Exception('failed to get continent')
        if not continent == None:
            continent = re.sub('#.*','', continent)
            continent = re.sub('\W','', continent)
            continent = re.sub('\d','', continent)

        #Trade Nodes
        trade_files = glob(self.settings[0]+r'common\tradenodes'+'\*.txt')
        check=-1
        for trade_file in trade_files:
            if check<0:
                trade_lines = []
                with open(trade_file, 'r') as trade: #Settings
                    trade_lines = trade.readlines()
                    trade.close()
                for i,line in enumerate(trade_lines):
                    if re.search(f'\D{id}\D', line):
                        loop=True
                        counter=0
                        try:
                            while loop:
                                if re.search('location', trade_lines[i+counter]):
                                    trade_node=trade_lines[i+counter-1]
                                    loop=False
                                    check=1
                                counter-=1
                        except:
                            return Exception('failed to get continent')
        if not trade_node == None:
            trade_node = re.sub('#.*','', trade_node)
            trade_node = re.sub('\W','', trade_node)
            trade_node = re.sub('\d','', trade_node)
        self.arc_info = [area, region, continent, trade_node]

    def set_acr(self, prov_list, arc, set_name):
        if arc ==0:
            self.arc_weird_bool=not self.arc_weird_bool
            if self.arc_weird_bool:
                #Area
                area_lines = []
                with open(self.settings[0]+r'map\area.txt') as areas: #Settings
                    area_lines = areas.readlines()
                    areas.close()
                copy_area_lines=area_lines
                for prov in prov_list:
                    for n,line in enumerate(area_lines):
                        if re.search(' '+prov+' ' or '\t'+prov+' ' or ' '+prov+'\n', line):
                            copy_area_lines[n]=re.sub(r'\b'+prov+r'\b','', line)
                if set_name == None:
                    letters = string.ascii_lowercase
                    area_name=f'{choice(letters)}{choice(letters)}{choice(letters)}{choice(letters)}{choice(letters)}{choice(letters)}_area'
                    prov_list=f'{prov_list}'
                    provs=re.sub('\'', '', prov_list)
                    provs=re.sub(']', '', provs)
                    provs=re.sub('\[', '', provs)
                    provs=re.sub(']', '', provs)
                    provs=re.sub(',', '', provs)
                    new_line=f'\n{area_name}'+'={ #Added with Modding Overhaul\n'+'\t'+provs+'\n}'+'\n'
                    copy_area_lines.append(new_line)
                else:
                    for n, line in enumerate(area_lines):
                        if re.search (set_name, line):
                            prov_list=f'{prov_list}'
                            provs=re.sub('\'', '', prov_list)
                            provs=re.sub(']', '', provs)
                            provs=re.sub('\[', '', provs)
                            provs=re.sub(']', '', provs)
                            provs=re.sub(',', '', provs)
                            copy_area_lines.insert(n+1,'\t'+provs+'\n')
                file = open(self.settings[0]+r'map\area.txt','w') #Settings
                file.writelines(copy_area_lines)
                file.close()
                print('added')
        elif arc == 1:
            self.arc_weird_bool=not self.arc_weird_bool
            if self.arc_weird_bool:
                #Continent
                continent_lines = []
                with open(self.settings[0]+r'map\continent.txt') as continents: #Settings
                    continent_lines = continents.readlines()
                copy_continent_lines=continent_lines
                for prov in prov_list:
                    for n,line in enumerate(continent_lines):
                        if re.search(' '+prov+' ' or '\t'+prov+' ' or ' '+prov+'\n' or f'location={prov}', line):
                            copy_continent_lines[n]=re.sub(r'\b'+prov+r'\b','', line)
                if set_name == None:
                    letters = string.ascii_lowercase
                    continet_name=f'{choice(letters)}{choice(letters)}{choice(letters)}{choice(letters)}{choice(letters)}{choice(letters)}'
                    prov_list=f'{prov_list}'
                    provs=re.sub('\'', '', prov_list)
                    provs=re.sub(']', '', provs)
                    provs=re.sub('\[', '', provs)
                    provs=re.sub(']', '', provs)
                    provs=re.sub(',', '', provs)
                    new_line=f'\n{continet_name}'+'={ #Added with Modding Overhaul\n'+'\t'+provs+'\n}'+'\n'
                    copy_continent_lines.append(new_line)
                else:
                    for n, line in enumerate(continent_lines):
                        if re.search (set_name, line):
                            prov_list=f'{prov_list}'
                            provs=re.sub('\'', '', prov_list)
                            provs=re.sub(']', '', provs)
                            provs=re.sub('\[', '', provs)
                            provs=re.sub(']', '', provs)
                            provs=re.sub(',', '', provs)
                            copy_continent_lines.insert(n+1,'\t'+provs+'\n')
                file = open(self.settings[0]+r'map\continent.txt','w') #Settings
                file.writelines(copy_continent_lines)
                file.close()
                print('added', set_name)
        elif arc == 2:
            self.arc_weird_bool=not self.arc_weird_bool
            if self.arc_weird_bool and not set_name == None:
                trade_files = glob(self.settings[0]+r'common\tradenodes'+'\*.txt')
                for trade_file in trade_files:
                    trade_lines = []
                    with open(trade_file) as t_file: #Settings
                        trade_lines = t_file.readlines()
                    copy_trade_lines=trade_lines
                    copy_prov_list = prov_list
                    copy_prov_list[0] = ' '+prov_list[0]
                    copy_prov_list[len(prov_list)-1] = prov_list[len(prov_list)-1]+' '
                    prov_str = ' | '.join(copy_prov_list)
                    for double_check in range(2):
                        for n,line in enumerate(trade_lines):
                            if re.search(prov_str, line): #broken
                                copy_trade_lines[n]=re.sub(prov_str,' ', line)
                    for n, line in enumerate(trade_lines):
                        if re.search (set_name+'={', line):
                            t_check=True
                            t_counter=1
                            while t_check:
                                if re.search('members', copy_trade_lines[n+t_counter]):
                                    prov_list=f'{prov_list}'
                                    provs=re.sub('\'', '', prov_list)
                                    provs=re.sub(']', '', provs)
                                    provs=re.sub('\[', '', provs)
                                    provs=re.sub(']', '', provs)
                                    provs=re.sub(',', '', provs)
                                    copy_trade_lines.insert(n+t_counter+1,'\t\t'+provs+'\n')
                                    t_check=False
                                else:
                                    t_counter+=1
                    file = open(trade_file,'w') #Settings
                    file.writelines(copy_trade_lines)
                    file.close()
                print('added', set_name)

    def combine_arc(self):
        self.arc_weird_bool=not self.arc_weird_bool
        if self.arc_weird_bool:
            shape=np.shape(self.definitions)
            num_list = [ i for i in range(shape[0]+1)]
            area_line='\nall_areas = {\n\t'+f'{num_list}'+'\n}\n'
            area_line=area_line.replace(',','')
            area_line=area_line.replace('[','')
            area_line=area_line.replace(']','')
            with open(self.settings[0]+r'map\area.txt', 'w+') as area_file: #SETTINGS
                area_file.write(area_line)
            continent_line='\nall_continents = {\n\t'+f'{num_list}'+'\n}\n'
            continent_line=continent_line.replace(',','')
            continent_line=continent_line.replace('[','')
            continent_line=continent_line.replace(']','')
            with open(self.settings[0]+r'map\continent.txt', 'w+') as continent_file: #SETTINGS
                continent_file.write(continent_line)
            region_line='\nall_region = {\n\tareas = {\n\t\tall_areas\n\t}\n}\n'
            with open(self.settings[0]+r'map\region.txt', 'w+') as region_file: #SETTINGS
                region_file.write(region_line)
            
    def command_prompt(self, command, ids):
        if command == 'print':
            np.savetxt(self.start_path+'/Modding Overhaul/new_files/province_groups.txt',ids,fmt='%s')
        else:
            try:
                commands = command.split(';')
                cmd_1 = commands[0].split(',')
                cmd_2 = commands[1].split(',')
            except:
                Exception('failed to understand command format')
                return
            province_file_names = glob(self.settings[0]+r'history\provinces'+'\*.txt') #Settings
            name = None
            for id in ids:
                for name in province_file_names:
                    real_name = name.replace(self.settings[0]+r'history\provinces'+'\\', '') #Settings

                    prov_name = real_name.replace(f'{id}', '')
                    prov_name = prov_name.replace(f'-', '')
                    prov_name = prov_name.replace('.txt', '')

                    match_one = re.search(f'^{id}-', real_name)
                    match_two = re.search(f'^{id} -', real_name)
                    match_three = re.search(f'^{id}.txt', real_name)

                    if match_one or match_two or match_three:
                        break
                prov_lines = []
                try:
                    with open(name) as prov:
                        prov_lines = prov.readlines()
                except:
                    Exception(f'Failed to find path {name}')
                lines_copy = prov_lines
                if len(commands)==2 and commands[1]=='d':
                    print('done')
                    trigger_check = False
                    for line in prov_lines:
                        if line == (commands[0]+'\n'):
                            trigger_check = True
                    if trigger_check:
                        for c, cmd in enumerate(cmd_1):
                            match = False
                            for n, line in enumerate(lines_copy):
                                if re.match(cmd, line):
                                    match = True
                                    prov_lines.pop(n)
                elif len(commands)>2 and commands[2]=='k':
                    for c, cmd in enumerate(cmd_1):
                        prov_lines.append('\n'+cmd_1[c]+' = '+cmd_2[c])
                elif len(commands)>2 and commands[2]=='r':
                    for c, cmd in enumerate(cmd_1):
                        match = False
                        for n, line in enumerate(lines_copy):
                            if re.match(cmd, line):
                                match = True
                                prov_lines.pop(n)
                                prov_lines.insert(n, cmd_1[c]+' = '+cmd_2[c]+'\n')
                        if not match:
                            prov_lines.append('\n'+cmd_1[c]+' = '+cmd_2[c])
                elif len(commands)>2 and re.search('[a-zA-Z]', commands[2]):
                    trigger_check = False
                    for line in prov_lines:
                        if line == (commands[2]+'\n') or re.match(line, commands[2]+r'\Z'):
                            trigger_check = True
                    if trigger_check:
                        for c, cmd in enumerate(cmd_1):
                            match = False
                            for n, line in enumerate(lines_copy):
                                if re.match(cmd, line):
                                    match = True
                                    prov_lines.pop(n)
                                    prov_lines.insert(n, cmd_1[c]+' = '+cmd_2[c]+'\n')
                            if not match:
                                prov_lines.append('\n'+cmd_1[c]+' = '+cmd_2[c])
                elif len(commands)>2:
                    date = commands[2]
                    for c, cmd in enumerate(cmd_1):
                        prov_lines.append('\n'+date+' = { '+cmd_1[c]+' = '+cmd_2[c]+' }')
                else:
                    for c, cmd in enumerate(cmd_1):
                        match = False
                        for n, line in enumerate(lines_copy):
                            if re.match(cmd, line):
                                match = True
                                prov_lines.pop(n)
                                prov_lines.insert(n, cmd_1[c]+' = '+cmd_2[c]+'\n')
                        if not match:
                            prov_lines.append('\n'+cmd_1[c]+' = '+cmd_2[c])


                file = open(name,'w') #Settings
                file.writelines(prov_lines)
                file.close()
                print(f'finished: {name}')

    def get_map_info(self):
        image, index = np.unique(np.asarray(self.province_bmp).reshape(-1, 3), axis=0, return_index = True)

    def create_prov_files(self):
        if not os.path.exists(self.settings[0]+r'history/provinces'):
            os.makedirs(self.settings[0]+r'history/provinces')
        province_file_names = glob(self.settings[0]+r'history/provinces'+'/*.txt') #Settings
        ids=[d[0] for d in self.definitions]
        for file_names in province_file_names:
            id=re.sub(r'.*history\D{1,99}(\d{1,99})\D{1,99}',r'\1',file_names)
            if id in ids:
                ids.pop(ids.index(id))
        print(f'Creating {len(ids)} province files')
        for i in ids:
            open(self.settings[0]+r'history\provinces'+f'\{i}.txt', 'x')