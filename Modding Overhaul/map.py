import numpy as np
import time
import pygame as pg
import pickle
from multiprocessing import Array

class Province():
    def __init__(self, color, id):
        self.color_str = [str(color[0]), str(color[1]), str(color[2])]
        self.color = color
        self.id = id
        self.indices = []
        self.p_data = np.array([])
        self.c_data = np.array([])
        self.r_data = np.array([])

    def get_indices(self, map):
        self.indices = []
        self.indices = np.argwhere((np.array(map[:,:], dtype=str)==self.color).all(axis=2))

    def color_map(self, colors, map):
        if colors == 1: #Development
            tot_dev = 3
            print(tot_dev, 'dev')
            blank=np.zeros(np.shape(map))
            self.get_indices(map)
            for i in self.indices:
                blank[i[0],i[1]] = [tot_dev,127,0]
            return map, pg.surfarray.make_surface(blank)
    
def save_provinces(Provinces):
    now=time.perf_counter()
    print('Saving')
    for province in Provinces:
        with open(f'Provinces\\{province.id}.obj', 'wb', buffering=(2<<16) + 8) as file:
            pickle.dump(province, file)
        print(province.id, time.perf_counter()-now)

def collect_provinces(map, colors, info):
    return [Province(color, info.get_province_id([str(color[0]), str(color[1]), str(color[2])])) for color in colors]

def set_province_info(info, province):
    province.p_data = np.array([info.get_province_info(province.id)])
    province.c_data = np.array([info.find_country_info(province.id)])
    province.r_data = np.array([info.get_region_info(province.id)])