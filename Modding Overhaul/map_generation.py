import numpy as np
import pygame as pg
from random import randint, uniform, shuffle
import cv2
import time
from noise import pnoise2
from PIL import Image, ImageOps
import os
from collections import OrderedDict as od
import re
from math import log2
from matplotlib.colors import Normalize
from functools import reduce
from matplotlib import cm
import matplotlib.pyplot as plt
from skimage import color
from scipy.spatial import Voronoi
from moviepy.video.io.bindings import mplfig_to_npimage
import pandas as pd
from lloyd import Field

class height_map_gen:
    def __init__(self, height, width): #switched height and width
        self.start_path=os.path.split(os.path.dirname(__file__))[0]
        self.start_path=self.start_path.replace('\\','/')
        self.start_path=self.start_path.replace('//','/')
        self.settings=np.genfromtxt(self.start_path+'/Modding Overhaul/SETTINGS.txt', skip_header=4, dtype='str',delimiter=';')
        self.definitions = []
        try:
            self.pic = np.array(Image.open(self.settings[0]+'map/heightmap.bmp')) #Settings
        except:
            print('failed to open:' + self.settings[0] + 'map/heightmap.bmp')
            self.pic = Image.open('C:\\Program Files (x86)\\Steam\\steamapps\\common\\Europa Universalis IV\\map\\heightmap.bmp')
        self.edit = self.pic
        try:
            self.p_pic = np.array(Image.open(self.settings[0]+'map/provinces.bmp'))
        except:
            self.p_pic = Image.open('C:\\Program Files (x86)\\Steam\\steamapps\\common\\Europa Universalis IV\\map\\provinces.bmp')
        try:
            self.t_pic = Image.open(self.settings[0]+'map/terrain.bmp')
        except:
            self.t_pic = Image.open('C:\\Program Files (x86)\\Steam\\steamapps\\common\\Europa Universalis IV\\map\\terrain.bmp')
        self.pedit = self.p_pic
        self.c_pic = []
        self.n_pic = None
        self.mask = None
        self.pic_f=None
        self.p_pic_f=None
        self.width = np.shape(self.pic)[1]
        self.height = np.shape(self.pic)[0]
        self.win_width = width
        self.win_height = height
        self.noise = False
        self.province = False
        self.cs = False
        self.tb = False
        self.counters = None

    def array_to_bkgrnd(self, array):
        try:
            if np.shape(array)[2] == 3:
                if not np.shape(array)[0] == self.width:
                    array = cv2.flip(array, 0)
                    array = cv2.rotate(array, cv2.ROTATE_90_CLOCKWISE)
                array = cv2.resize(array, (self.win_width,self.win_height), interpolation=cv2.INTER_LANCZOS4)
        except:
            array = array[..., np.newaxis]
            array = np.repeat(array, 3, 2)
            array = cv2.flip(array.astype(np.uint8), 0)
            array = cv2.rotate(array, cv2.ROTATE_90_CLOCKWISE)
            array = cv2.resize(array, (self.win_width,self.win_height), interpolation=cv2.INTER_LANCZOS4)
        return pg.surfarray.make_surface(array)

    def post_proccessing(self, pic):
        print('post_proccessing')
        self.pic = (pic-np.min(pic))/np.ptp(pic)
        #self.pic = np.where(self.pic<.5,self.pic, self.pic-((1-1/(self.pic*2))/2))
        #self.pic = (self.pic-np.min(self.pic))/np.ptp(self.pic)
        self.pic = ((self.pic*240)+10).astype(np.uint8)
        self.pic = self.pic[..., np.newaxis]
        self.pic = np.repeat(self.pic, 3, 2)
        flip = randint(-1,3)
        if flip<2:
            self.pic = cv2.flip(self.pic, flip)
        self.pic = self.testers(self.pic)
        contrast=-15
        self.pic = cv2.addWeighted(self.pic, 131*(contrast + 127)/(127*(131-contrast)), self.pic, 0, 127*(1-(131*(contrast + 127)/(127*(131-contrast)))))
        background = cv2.resize(self.pic, (self.win_width,self.win_height), interpolation=cv2.INTER_LANCZOS4)
        self.pic = cv2.resize(self.pic, (self.height,self.width), interpolation=cv2.INTER_LANCZOS4)
        self.edit = self.pic
        background = pg.surfarray.make_surface(background)
        self.noise = True
        return background
    
    def generate_heightmap(self, m, s, o, p, l, warps):
        print(m, s, o, p, l, warps)
        pic, warpers = self.get_noise(m, s, o, p, l, warps)
        pic = self.warper(pic, warpers)
        background = self.post_proccessing(pic)
        print('-')
        return background

    def get_noise(self, m, s, o, p, l, warps):
        print('noise')
        #Prep
        shape = (2**m, 2**m)

        pic=[[self.noise_getter(i, i/s, j/s, shape, 6*(2**o), p, l) for j in range(shape[1])] for i in range(shape[0])]
        pic = (pic-np.min(pic))/np.ptp(pic)
        s, o, p, l = randint(150,450),randint(2,3),round(uniform(0.35,.65),2),randint(2,3)
        print(m, s, o, p, l)
        warpers = [np.asarray([[self.noise_getter(i, i/s, j/s, shape, 6*(2**o), p, l) for j in range(shape[1])] for i in range(shape[0])]) for i in range(warps)]
        return np.asarray(pic), warpers

    def noise_getter(self, i, scaledi, scaledj, shape, octaves, persistance, lacunarity):
        noise_val = pnoise2(scaledi,scaledj,octaves=octaves,persistence=persistance,lacunarity=lacunarity,repeatx=shape[0],repeaty=shape[1],base=0)
        return abs(2*(noise_val*round(1-(((i-shape[0]/2)**2)/((shape[0]/2)**2)),3)))+0.5
    
    def warper(self, pic, warpers):
        scale=1
        fall=-round(uniform(0.5,0.8),4)
        print('warping', fall)
        for w,warp in enumerate(warpers):
            warp = np.asarray(((warp-np.min(warp))/np.ptp(warp))*np.shape(pic)[0])
            for x in range(np.shape(pic)[0]):
                for y in range(np.shape(pic)[0]):
                    pic[x,y] = pic[min(int(x+(scale*warp[x,y])),np.shape(pic)[0]-1),min(int(y+(scale*warp[x,y])),np.shape(pic)[0]-1)]
            scale*=fall
            pic=cv2.addWeighted(abs(randint(0,1)-warp),1,pic,1/(w+1),0)
        return pic

    def testers(self, pic):
        return abs(pic)

    def diamond_square(self):
        print('plasma')
        heightmapWidth = 2**(10) + 1

        # initialize the heightmap to 0's
        heightmap = np.zeros((heightmapWidth,heightmapWidth))
        # set the corner points to the same random value
        heightmap[0][0] = randint(0, 255)
        heightmap[heightmapWidth - 1][0] = randint(0, 255)
        heightmap[0][heightmapWidth - 1] = randint(0, 255)
        heightmap[heightmapWidth - 1][heightmapWidth - 1] = randint(0, 255)

        # set the randomness bounds, higher values mean rougher landscapes
        randomness = 150
        tileWidth = heightmapWidth - 1

        # we make a pass over the heightmap
        # each time we decrease the side length by 2
        while tileWidth > 1:
            halfSide = tileWidth // 2

            # set the diamond values (the centers of each tile)
            for x in range(0, heightmapWidth - 1, tileWidth):
                for y in range(0, heightmapWidth - 1, tileWidth):
                    cornerSum = heightmap[x][y] + \
                                heightmap[x + tileWidth][y] + \
                                heightmap[x][y + tileWidth] + \
                                heightmap[x + tileWidth][y + tileWidth]

                    avg = cornerSum / 4
                    avg += randint(-randomness, randomness)

                    heightmap[x + halfSide][y + halfSide] = int(avg)

            # set the square values (the midpoints of the sides)
            for x in range(0, heightmapWidth - 1, halfSide):
                for y in range((x + halfSide) % tileWidth, heightmapWidth - 1, tileWidth):
                    avg = heightmap[(x - halfSide + heightmapWidth - 1) % (heightmapWidth - 1)][y] + \
                        heightmap[(x + halfSide) % (heightmapWidth - 1)][y] + \
                        heightmap[x][(y + halfSide) % (heightmapWidth - 1)] + \
                        heightmap[x][(y - halfSide + heightmapWidth - 1) % (heightmapWidth - 1)]

                    avg /= 4.0
                    avg += randint(-randomness, randomness)

                    heightmap[x][y] = int(avg)

                    # because the values wrap round, the left and right edges are equal, same with top and bottom
                    if x == 0:
                        heightmap[heightmapWidth - 1][y] = int(avg)
                    if y == 0:
                        heightmap[x][heightmapWidth - 1] = int(avg)

            # reduce the randomness in each pass, making sure it never gets to 0
            randomness = max(randomness // 2, 1)
            tileWidth //= 2

        heightmap = np.where(heightmap>255, 255, heightmap)
        heightmap = np.where(heightmap<=0, 1, heightmap)
        heightmap = heightmap[..., np.newaxis]
        heightmap = np.repeat(heightmap, 3, 2)
        background = cv2.resize(heightmap, (self.win_width, self.win_height), interpolation=cv2.INTER_LANCZOS4)
        self.noise = True
        heightmap = cv2.resize(heightmap, (self.height, self.width), interpolation=cv2.INTER_LANCZOS4)
        heightmap = heightmap.astype(np.uint8)
        self.pic = heightmap
        background = pg.surfarray.make_surface(background)
        print('finished')
        print(heightmap[0,0], np.max(heightmap), np.min(heightmap))
        return background

    def voronoi_province_map(self):
        now=time.perf_counter()
        def generate_voroni(self, NumOfPoints, low, big, mask, now):
            start_num = int(NumOfPoints*1.5)
            base=np.zeros((start_num,2))
            x = np.random.randint(0,self.width,size=(start_num))
            y = np.random.randint(0,self.height,size=(start_num))
            base[:,0] = x
            base[:,1] = y
            points = base

            def remove_filiter_points(NumOfPoints,x,y):

                # Bin points onto a rectangular grid with approximately "subset_num" cells
                subset_num = NumOfPoints
                nbins = int(np.sqrt(subset_num))
                xbins = np.linspace(x.min(), x.max(), nbins+1)
                ybins = np.linspace(y.min(), y.max(), nbins+1)

                # Make a dataframe indexed by the grid coordinates.
                i, j = np.digitize(y, ybins), np.digitize(x, xbins)
                df = pd.DataFrame(dict(x=x, y=y), index=[i, j])

                # Group by which cell the points fall into and choose a random point from each
                groups = df.groupby(df.index)
                new = groups.agg(lambda x: np.random.permutation(x)[0])

                base = np.zeros((np.shape(new.x)[0],2))
                base[:,0] = new.x
                base[:,1] = new.y
                points = base

                return points, new.x, new.y
            
            
            points, x, y = remove_filiter_points(NumOfPoints,x,y)
            #points = np.asarray([n for i,n in enumerate(points) if ((n[0]-points[-1][0])**2 + (n[1]-points[-1][1])**2)**.5 >= 500])

            field = Field(points)

            for i in range(2):
                field.relax()
            points = field.get_points()

            print(np.shape(points), time.perf_counter()-now)

            mask = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)
            #mask = cv2.flip(mask, 0)

            contours = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0]
            points = np.array([point for point in points if any(np.where(np.asarray([cv2.pointPolygonTest(contour, point, False) for contour in contours])==-1,False,True))])

            #field = Field(points)
            #field.relax()
            #points = field.get_points()

            print(np.shape(points), time.perf_counter()-now)

            #Voronoi Diamgram
            vor = Voronoi(points)
            def voronoi_finite_polygons_2d(vor, mask, radius=None):
                if vor.points.shape[1] != 2:
                    raise ValueError("Requires 2D input")

                new_regions = []
                new_vertices = vor.vertices.tolist()

                center = vor.points.mean(axis=0)
                if radius is None:
                    radius = vor.points.ptp().max()

                # Construct a map containing all ridges for a given point
                all_ridges = {}
                for (p1, p2), (v1, v2) in zip(vor.ridge_points, vor.ridge_vertices):
                    all_ridges.setdefault(p1, []).append((p2, v1, v2))
                    all_ridges.setdefault(p2, []).append((p1, v1, v2))

                # Reconstruct infinite regions
                for p1, region in enumerate(vor.point_region):
                    vertices = vor.regions[region]

                    if all(v >= 0 for v in vertices):
                        # finite region
                        new_regions.append(vertices)
                        continue

                    # reconstruct a non-finite region
                    ridges = all_ridges[p1]
                    new_region = [v for v in vertices if v >= 0]

                    for p2, v1, v2 in ridges:
                        if v2 < 0:
                            v1, v2 = v2, v1
                        if v1 >= 0:
                            # finite ridge: already in the region
                            continue

                        # Compute the missing endpoint of an infinite ridge

                        t = vor.points[p2] - vor.points[p1] # tangent
                        t /= np.linalg.norm(t)
                        n = np.array([-t[1], t[0]])  # normal

                        midpoint = vor.points[[p1, p2]].mean(axis=0)
                        direction = np.sign(np.dot(midpoint - center, n)) * n
                        far_point = vor.vertices[v2] + direction * radius

                        new_region.append(len(new_vertices))
                        new_vertices.append(far_point.tolist())

                    # sort region counterclockwise
                    vs = np.asarray([new_vertices[v] for v in new_region])
                    c = vs.mean(axis=0)
                    angles = np.arctan2(vs[:,1] - c[1], vs[:,0] - c[0])
                    new_region = np.array(new_region)[np.argsort(angles)]

                    # finish
                    new_regions.append(new_region.tolist())

                return new_regions, np.asarray(new_vertices)

            # Plots
            fig = plt.figure(frameon=False, dpi=1024)
            regions, vertices = voronoi_finite_polygons_2d(vor, mask)
            fig.set_size_inches(5.5, 2)

            # Fills in Color
            for region in regions:
                polygon = vertices[region]
                plt.fill(*zip(*polygon),c=(uniform(0,0.99),uniform(0,0.99),uniform(low,big)),antialiased=False)

            #plt.xlim(vor.min_bound[0], vor.max_bound[0])
            #plt.ylim(vor.min_bound[1], vor.max_bound[1])
            plt.axis('off')
            plt.imshow(mask)
            voroloid = mplfig_to_npimage(fig)
            voroloid = voroloid[246:1824,718:5055]

            return voroloid

        #Set-up
        try:
            if np.shape(self.pic)[2]==3:
                pic=cv2.rotate(self.pic, cv2.ROTATE_90_COUNTERCLOCKWISE)
                pic=cv2.flip(pic, 0)
        except:
            try:
                pic = self.pic[..., np.newaxis]
                pic = np.repeat(pic, 3, 2)
            except:
                pic=self.pic
        if not np.shape(pic)[0] == self.height:
            print('working')
            pic = cv2.rotate(pic, cv2.ROTATE_90_COUNTERCLOCKWISE)
            pic = cv2.flip(pic, 0)
        print(np.shape(pic))
        self.mask=np.where(np.asarray(pic).astype(np.uint8)>=94,50,1).astype(np.uint8)

        #Land generation
        mask=np.where(np.asarray(self.mask).astype(np.uint8)==50,[255,255,255],0).astype(np.uint8)
        voroloid = generate_voroni(self, 3000, 0, 0.45, mask, now) #Function
        print(np.shape(voroloid))
        voroloid=cv2.resize(voroloid, (int(self.width/1.8),int(self.height/1.8)), interpolation=cv2.INTER_NEAREST_EXACT)
        voroloid=cv2.resize(voroloid, (self.width,self.height), interpolation=cv2.INTER_NEAREST_EXACT)
        land=np.where(np.asarray(self.mask).astype(np.uint8)==50,voroloid,0).astype(np.uint8)
        print('land done', time.perf_counter()-now)

        #Sea generation
        mask=np.where(np.asarray(self.mask).astype(np.uint8)==1,[255,255,255],0).astype(np.uint8)
        voroloid = generate_voroni(self, int((self.width*self.height)/20000), 0.55, 0.99, mask, now) #Function
        voroloid=cv2.resize(voroloid, (int(self.width/4),int(self.height/4)), interpolation=cv2.INTER_NEAREST_EXACT)
        voroloid = cv2.resize(voroloid, (self.width,self.height), interpolation=cv2.INTER_NEAREST_EXACT)
        self.mask=np.where(np.asarray(pic).astype(np.uint8)>=94,50,1).astype(np.uint8)
        water=np.where(np.asarray(self.mask).astype(np.uint8)==1,voroloid,0).astype(np.uint8)
        print('water done', time.perf_counter()-now)

        #combine
        voroloid=cv2.add(land, water)
        self.p_pic=cv2.addWeighted(voroloid,0.5,self.mask,1, 0.0)
        self.province = True
        background = cv2.flip(self.p_pic, 0)
        background = cv2.rotate(background, cv2.ROTATE_90_CLOCKWISE)
        background = cv2.resize(background, (self.win_width, self.win_height), interpolation=cv2.INTER_NEAREST_EXACT)
        print('finished', time.perf_counter()-now)

        return pg.surfarray.make_surface(background)

    def make_province_map(self):
        try:
            print('started')
            timer=time.perf_counter()
            #Land vs Water
            pic=self.pic
            province_map=pic
            new_province_map=np.zeros((np.shape(province_map)[0],np.shape(province_map)[1],3)).astype(np.uint8)
            new_2_province_map=np.zeros((np.shape(province_map)[0],np.shape(province_map)[1],3)).astype(np.uint8)
            province_map=np.where(province_map.astype(np.uint8)>96,20,1).astype(np.uint8)
            
            # Square Maker
            print('making squares',time.perf_counter()-timer)
            shape=np.shape(new_province_map)
            for b in range((int(shape[0]/32))):
                q=randint(0,96)
                new_province_map[32*b:32*(b+1)][:]=[b+20,int(abs((b*2)-128)),abs(q-b)]
            for j in range((int(shape[0]/32))):
                q=randint(0,32)
                new_2_province_map[32*j:32*(j+1)][:]=[j+2,j,abs(128-j-q)]
            new_2_province_map=cv2.rotate(new_2_province_map, cv2.ROTATE_90_CLOCKWISE)
            new_2_province_map=cv2.resize(new_2_province_map, (shape[1],shape[0]), interpolation=cv2.INTER_NEAREST)
            new_3_province=cv2.add(new_province_map,new_2_province_map)
            new_3_province=cv2.rotate(new_3_province, cv2.ROTATE_90_CLOCKWISE)
            province_map=cv2.rotate(province_map, cv2.ROTATE_90_CLOCKWISE)
            self.mask=province_map
            province_map=cv2.add(new_3_province,province_map)
            province_map=cv2.flip(province_map, flipCode=1)
            self.p_pic=province_map.astype(np.uint8)
            background=cv2.rotate(self.p_pic, cv2.ROTATE_90_COUNTERCLOCKWISE)
            background=cv2.resize(background, (self.win_width,self.win_height), interpolation=cv2.INTER_LANCZOS4)
            background=cv2.flip(background,0)
            background = pg.surfarray.make_surface(background)
            self.province = True
            print('finished',time.perf_counter()-timer)
            return background
        except:
            timer=time.perf_counter()
            #Land vs Water
            pic = pic[..., np.newaxis]
            pic = np.repeat(pic, 3, 2)
            province_map=pic
            new_province_map=np.zeros((np.shape(province_map)[0],np.shape(province_map)[1],3)).astype(np.uint8)
            new_2_province_map=np.zeros((np.shape(province_map)[0],np.shape(province_map)[1],3)).astype(np.uint8)
            province_map=np.where(province_map.astype(np.uint8)>96,20,1).astype(np.uint8)
            
            # Square Maker
            print('making squares',time.perf_counter()-timer)
            shape=np.shape(new_province_map)
            for b in range((int(shape[0]/32))):
                q=randint(0,96)
                new_province_map[32*b:32*(b+1)][:]=[b+20,int(abs((b*2)-128)),abs(q-b)]
            for j in range((int(shape[0]/32))):
                q=randint(0,32)
                new_2_province_map[32*j:32*(j+1)][:]=[j+2,j,abs(128-j-q)]
            new_2_province_map=cv2.rotate(new_2_province_map, cv2.ROTATE_90_CLOCKWISE)
            new_2_province_map=cv2.resize(new_2_province_map, (shape[1],shape[0]), interpolation=cv2.INTER_NEAREST)
            new_3_province=cv2.add(new_province_map,new_2_province_map)
            new_3_province=cv2.rotate(new_3_province, cv2.ROTATE_90_CLOCKWISE)
            province_map=cv2.rotate(province_map, cv2.ROTATE_90_CLOCKWISE)
            province_map=cv2.add(new_3_province,province_map)
            province_map=cv2.flip(province_map, flipCode=1)
            province_map=cv2.rotate(province_map, cv2.ROTATE_90_CLOCKWISE)
            background=cv2.rotate(province_map.astype(np.uint8), cv2.ROTATE_90_COUNTERCLOCKWISE)
            background=cv2.resize(background, (self.win_width,self.win_height), interpolation=cv2.INTER_LANCZOS4)
            background = pg.surfarray.make_surface(background)
            province_map=cv2.rotate(province_map, cv2.ROTATE_90_CLOCKWISE)
            province_map=cv2.flip(province_map, flipCode=-1)
            self.p_pic = cv2.resize(province_map, (self.width,self.height), interpolation=cv2.INTER_LANCZOS4)
            self.province = True
            print('finished',time.perf_counter()-timer)
            return background

    def drawImage(self, filename, rgbfun, n, m):
        colormat = np.zeros((n, m, 3), dtype=float)
        for i in range(n):
            for j in range(m):
                rgb01 = rgbfun(i, j) # rgb(a) values in [0,1]
                for k in range(3):
                    colormat[i,j,k] = int(255 * rgb01[2-k])
        print('finished')
        colormat = color.rgb2gray(colormat)
        colormat = colormat[..., np.newaxis]
        colormat = np.repeat(colormat, 3, 2)
        colormat = cv2.medianBlur(colormat.astype('float32'),3)
        background = cv2.resize(colormat, (self.win_width, self.win_height), interpolation=cv2.INTER_NEAREST)
        background = pg.surfarray.make_surface(background)
        colormat = np.swapaxes(colormat,1,0)
        colormat = cv2.resize(colormat, (self.width, self.height), interpolation=cv2.INTER_NEAREST)
        cv2.imwrite(self.start_path+'/Modding Overhaul/new_files/fractal.bmp',colormat)
        return background

    def mapToComplexPlaneCenter(self, n, m, c, r, i, j):
        return c + r * complex(2 * j / n - 1, 2 * i / m - 1)

    def demMandelbrot(self, c, K, overflow):
        ck, dk = c, 1
        for _ in range(K):
            if max(
                abs(ck.real), abs(ck.imag),
                abs(dk.real), abs(dk.imag)
            ) > overflow: break # so computer doesn't crash
            dk *= 2 * ck
            dk += 1
            ck *= ck
            ck += c
        absck = abs(ck)
        if absck <= 2: return 0
        else:
            absdk = abs(dk)
            if absdk == 0: return np.nan # this will probably never happen
            estimate = log2(absck) * absck / absdk
            return -log2(estimate)

    def horner(self, p, z):
        return reduce(lambda x, y: x * z + y, p)

    def differentiate(self, poly):
        return [(len(poly) - 1 - i) * an for (i, an) in enumerate(poly[:-1])]

    def radiusJulia(self, poly, L=1.0000001):
        an = abs(poly[0])
        C = sum(map(abs, poly)) - an
        return max(1, 2 * C / 2, pow(2 * L / an, 1 / (len(poly) - 1-1)))

    def demJulia(self, p, dp, z, K, R, overflow):
        zk, dk = z, 1
        for _ in range(K):
            if max(
                abs(zk.real), abs(zk.imag),
                abs(dk.real), abs(dk.imag)
            ) > overflow: break
            dk = self.horner(dp, zk) * dk
            zk = self.horner(p, zk)
        abszk = abs(zk)
        if abszk < R: return 0
        else:
            absdk = abs(dk)
            if absdk == 0: return np.nan
            estimate = log2(abszk) * abszk / absdk
            return -log2(estimate)


    def fractal(self, n, y, ctr, r, K, overflow, type):
        p=[randint(-1,1), randint(-1,1), uniform(-1,1)*(randint(-3,3)+1j)]
        dp = self.differentiate(p)
        s = self.radiusJulia(p)
        print(ctr,r,K,p,type)
        colormaps = [cm.magma.reversed(), cm.inferno.reversed(), cm.cubehelix.reversed()] 
        colormap = colormaps[randint(0,len(colormaps)-1)]
        if type == 0:
            arr = np.reshape(np.asarray([self.demMandelbrot(self.mapToComplexPlaneCenter(n, y, ctr, r, i, j), K, overflow) for j in range(n) for i in range(y)], dtype=float), (n,y))
        else:
            arr = np.reshape(np.asarray([self.demJulia(p, dp, self.mapToComplexPlaneCenter(n, y, ctr, r, i, j), K, s, overflow) for j in range(n) for i in range(y)], dtype=float), (n,y))
        print('done mapping')

        m, M = arr.min(), arr.max()
        arr[arr == 0] = M # 0 only denotes the inner set and it could spoil our normalization
        arr[arr == np.nan] = m # we don't care, this happens too rarely, if at all
        if type == 0:
            colortable = colormap(Normalize(m, M)(arr))
        else:
            normalized = Normalize(m, M)(arr)
            adjusted = pow(normalized, ctr) # explained below
            colortable = colormap(adjusted)

        def rgbfun(i, j):
            if arr[i,j] == M: return (0,0,0)
            else: return colortable[i,j]

        print('Drawing')
        background = self.drawImage('demMandelbrot.png', rgbfun, n, y)
        return background


    def just_def(self, province=True):
        if province:
            province_map = Image.open(self.settings[0]+'map/provinces.bmp') #settings
        else:
            province_map=Image.fromarray(self.p_pic)
        pixels = list(province_map.getdata())
        pixels = list(od.fromkeys(pixels))
        pixels = np.asarray(pixels)
        rgb = []
        for i,x in enumerate(pixels):
            n = i
            r = pixels[i,0]
            g = pixels[i,1]
            b = pixels[i,2]
            nrgb = f'{n+1};{r};{g};{b};x;x'
            rgb = np.append(rgb, nrgb)
        self.definitions=rgb
        np.savetxt(self.start_path+'/Modding Overhaul/new_files/definition.csv', rgb, fmt='%s') #Settings
        print('defs')

    def color_maps(self):
        try:
            self.t_pic=self.t_pic.convert('RGB')
            self.t_pic1=Image.new(self.t_pic.mode, (self.t_pic.size[0]*2, self.t_pic.size[1]), (0,0,0))
            self.t_pic1.paste(self.t_pic)
            self.t_pic=self.t_pic1
            self.t_pic.save(self.start_path+'/Modding Overhaul/new_files/terrain.jpg')
            mainPix()
            self.t_pic=Image.open(self.start_path+'/Modding Overhaul/new_files/colormaps/images/terrain-outputs.png').convert('RGB')
            self.t_pic=self.t_pic.resize((2816,1024), Image.Resampling.NEAREST)
            os.remove(self.start_path+'/Modding Overhaul/new_files/colormaps/images/terrain-inputs.png')
            os.remove(self.start_path+'/Modding Overhaul/new_files/colormaps/images/terrain-outputs.png')
            os.remove(self.start_path+'/Modding Overhaul/new_files/colormaps/images/terrain-targets.png')
            self.t_pic.save(self.start_path+'/Modding Overhaul/new_files/colormap.jpg')
        except:
            self.old_color_maps() 


    def old_color_maps(self):
        works=True
        winter_tint=np.zeros((np.shape(self.pic)[0],np.shape(self.pic)[1],3))
        water_tint=np.zeros((np.shape(self.pic)[0],np.shape(self.pic)[1],3))
        spring_tint=np.zeros((np.shape(self.pic)[0],np.shape(self.pic)[1],3))
        summer_tint=np.zeros((np.shape(self.pic)[0],np.shape(self.pic)[1],3))

        winter_tint[:,:]=[80,100,80]
        water_tint[:,:]=[80,100,140]
        spring_tint[:,:]=[70,90,60]
        summer_tint[:,:]=[65,70,30]

        pic=self.pic

        try:
            winter_map=cv2.add(np.copy(self.pic),winter_tint.astype(np.uint8))
        except:
            works=False
            pic = pic[..., np.newaxis]
            pic = np.repeat(pic, 3, 2)
            winter_map=cv2.add(np.copy(pic),winter_tint.astype(np.uint8))
        winter_map=np.where(pic.astype(np.uint8)>=96,winter_tint,water_tint)
        spring_map=np.where(pic.astype(np.uint8)>=96,spring_tint,water_tint)
        summer_map=np.where(pic.astype(np.uint8)>=96,summer_tint,water_tint)
        print(np.shape(winter_map))

        self.mask=np.where(pic.astype(np.uint8)>=96,50,1).astype(np.uint8)
        self.mask=cv2.rotate(self.mask, cv2.ROTATE_90_CLOCKWISE)
        self.mask=cv2.flip(self.mask, flipCode=1)
        self.mask=cv2.rotate(self.mask, cv2.ROTATE_90_CLOCKWISE)
    
        water_tint=np.zeros_like(self.mask)
        water_tint[:,:]=[80,100,140]
        water_map=cv2.add(self.mask,water_tint.astype(np.uint8))
        background=np.swapaxes(spring_map,1,0)
        background=background.astype(np.uint8)

        if works:
            water_map=np.swapaxes(water_map,1,0)
            water_map=cv2.flip(water_map,0)
            water_map = Image.fromarray(water_map)

            winter_map=np.swapaxes(winter_map,1,0)

            spring_map=np.swapaxes(spring_map,1,0)
            background=spring_map.astype(np.uint8)
            spring_map = Image.fromarray(spring_map)

            summer_map=np.swapaxes(summer_map,1,0)
            summer_map = Image.fromarray(summer_map)
            self.c_pic = [water_map,winter_map,spring_map,summer_map]
            background=cv2.rotate(background, cv2.ROTATE_90_CLOCKWISE)
            background=cv2.flip(background,1)
            background=cv2.resize(background, (self.win_width,self.win_height), interpolation=cv2.INTER_LANCZOS4)
            background = pg.surfarray.make_surface(background)
        else:
            winter_map = Image.fromarray(np.asarray(winter_map).astype(np.uint8))
            summer_map = Image.fromarray(np.asarray(summer_map).astype(np.uint8))
            water_map = cv2.flip(water_map, 1)
            water_map = Image.fromarray(np.asarray(water_map).astype(np.uint8))
            spring_map = Image.fromarray(np.asarray(spring_map).astype(np.uint8))
            self.c_pic = [water_map,winter_map,spring_map,summer_map]
            background=cv2.resize(background, (self.win_width,self.win_height), interpolation=cv2.INTER_LANCZOS4)
            background = pg.surfarray.make_surface(background)

        print('finished')

        self.cs=True
        return background

    def terrain_base(self):
        print('starting terrain generation')
        works=True
        pic=self.pic
        try:
            tester=cv2.add(np.copy(self.pic).astype(np.uint8),self.mask.astype(np.uint8))
        except:
            try:
                if self.pic[0][0]<300:
                    pic = pic[..., np.newaxis]
                    pic = np.repeat(pic, 3, 2)
                    works=False
            except:
                None
        if not np.shape(pic) == (self.height, self.width,3):
            pic=cv2.resize(pic, (self.width, self.height))
        self.mask=np.where(pic.astype(np.uint8)>96,50,0).astype(np.uint8)
        terrain_base=np.zeros_like(self.mask)
        terrain_base[:,:]=[86,124,27]
        blue_mask=np.zeros_like(self.mask)
        blue_mask[:,:]=[8,31,130]
        blue_mask=np.where(pic.astype(np.uint8)<96,blue_mask,0).astype(np.uint8)
        def effect_terrainmap(self, pic, terrain_base, tint, height):
            terrain_base=np.where(pic.astype(np.uint8)>height,tint,terrain_base)
            print(f'{tint} effect done')
            return np.asarray(terrain_base).astype(np.uint8)
        print('starting noise')
        s, o, p, l = randint(150,450),randint(2,3),round(uniform(0.35,.65),2),2
        scale=4
        shape=(int(self.height/scale),int(self.width/scale))
        print(np.shape(terrain_base))
        desert=np.asarray([[self.noise_getter(i, i/s, j/s, shape, 6*(2**o), p, l) for j in range(shape[1])] for i in range(shape[0])])
        desert = np.array((desert-np.min(desert))/np.ptp(desert))*255
        desert = desert[..., np.newaxis]
        desert = np.repeat(desert, 3, 2)
        desert=cv2.resize(desert.astype(np.uint8), (self.height,self.width),interpolation=cv2.INTER_LANCZOS4)
        desert=cv2.rotate(desert, cv2.ROTATE_90_COUNTERCLOCKWISE)
        print(np.shape(desert))
        #Terrain Types & Pre-Effects
        print('beginning effects')
        terrain_base=effect_terrainmap(self, desert, terrain_base, [203,191,103], 185)
        terrain_base=effect_terrainmap(self, desert, terrain_base, [206,169,99], 200)
        terrain_base=effect_terrainmap(self, pic, terrain_base, [0,86,6], 185)
        terrain_base=effect_terrainmap(self, pic, terrain_base, [65,42,17], 215)
        terrain_base=effect_terrainmap(self, pic, terrain_base, [255,255,255], 230)
        #Effects
        #terrain_base=cv2.GaussianBlur(terrain_base,(11,11),cv2.BORDER_DEFAULT)
        #Add Masks
        terrain_base=np.where(pic.astype(np.uint8)>=96,terrain_base,0).astype(np.uint8)
        terrain_base=cv2.add(terrain_base,blue_mask)
    
        if works:
            terrain_base=np.swapaxes(terrain_base,1,0)
            background=terrain_base
            self.t_pic = Image.fromarray(terrain_base)
            background=cv2.rotate(background, cv2.ROTATE_90_CLOCKWISE)
            background=cv2.flip(background,1)
            background=cv2.resize(background, (self.win_width,self.win_height), interpolation=cv2.INTER_LANCZOS4)
            background = pg.surfarray.make_surface(background)
        else:
            self.t_pic = Image.fromarray(terrain_base)
            background=np.swapaxes(terrain_base,1,0)
            background=cv2.resize(background, (self.win_width,self.win_height), interpolation=cv2.INTER_LANCZOS4)
            background = pg.surfarray.make_surface(background)
        
        self.tb = True
        print('finished')

        return background

    def save_maps(self): #Settings
        if self.noise:
            self.pic_f=np.swapaxes(self.pic,1,0)
            height_map = Image.fromarray(self.pic_f, 'RGB')
            height_map.save(self.start_path+'/Modding Overhaul/new_files/heightmap.bmp',)
        if self.province:
            province_map = Image.fromarray(self.p_pic)
            province_map.save(self.start_path+'/Modding Overhaul/new_files/provinces.bmp',)
        if self.cs:
            self.c_pic[0].save(self.start_path+'/Modding Overhaul/new_files/water_map.bmp',)
            self.c_pic[1].save(self.start_path+'/Modding Overhaul/new_files/winter_map.bmp',)
            self.c_pic[2].save(self.start_path+'/Modding Overhaul/new_files/spring_map.bmp',)
            self.c_pic[3].save(self.start_path+'/Modding Overhaul/new_files/summer_map.bmp',)
            self.c_pic[2].save(self.start_path+'/Modding Overhaul/new_files/autumn_map.bmp',)
        if self.tb:
            self.t_pic.save(self.start_path+'/Modding Overhaul/new_files/terrain_base.bmp',)
        print('saved')

    def get_water_provinces(self):
        timer=time.perf_counter()
        self.mask=np.where(self.pic.astype(np.uint8)>=94,255,0).astype(np.uint8)
        self.mask=cv2.rotate(self.mask, cv2.ROTATE_90_CLOCKWISE)
        self.mask=cv2.flip(self.mask, flipCode=1)
        self.mask=cv2.rotate(self.mask, cv2.ROTATE_90_CLOCKWISE)
        try:
            if not np.shape(self.mask)[2] == 3:
                self.mask = self.mask[..., np.newaxis]
                self.mask = np.repeat(self.mask, 3, 2)
        except:
                self.mask = self.mask[..., np.newaxis]
                self.mask = np.repeat(self.mask, 3, 2)
        self.mask = cv2.flip(self.mask, 1)
        mask=Image.fromarray(np.uint8(self.mask))

        province_map = np.asarray(self.p_pic)
        province_map=cv2.subtract(np.asarray(province_map), self.mask)
        province_map=Image.fromarray(np.uint8(province_map))
        pixels = list(province_map.getdata())
        pixels = list(od.fromkeys(pixels))
        pixels = np.asarray(pixels)
        water_provinces = []
        rgb = []
        print(time.perf_counter()-timer)
        for i,x in enumerate(pixels):
            n = i
            r = pixels[i,0]
            g = pixels[i,1]
            b = pixels[i,2]
            nrgb = f'{r};{g};{b}'
            if not r==g==b<=0:
                rgb = np.append(rgb, nrgb)
        print(time.perf_counter()-timer)
        def_lines = []
        with open(self.settings[0]+r'map\definition.csv') as defs: #Settings
            def_lines = defs.readlines()
            defs.close()
        for color in rgb:
            s_water_provinces=[int(re.sub('\D','', re.sub(';\d{1,3};\d{1,3};\d{1,3};\D{1,99}','',line))) for line in def_lines if re.search(color, line)]
            water_provinces.append(s_water_provinces)
        print(time.perf_counter()-timer)
        water_provinces.insert(0, 'If it has more than one column ex:[1,2] then only choose the one that maches the prev and next in list')
        water_provinces=np.array(water_provinces)
        np.savetxt(self.start_path+'/Modding Overhaul/new_files/water_provinces.csv', water_provinces, fmt='%s') #Settings

    def edit_map(self, wand, radius, mouse, sign, map):
        if not map:
            background = self.edit
        else:
            background = self.pedit
        background=cv2.resize(background, (self.win_height,self.win_width), interpolation=cv2.INTER_LANCZOS4)
        background=cv2.rotate(background, cv2.ROTATE_90_CLOCKWISE)
        background=cv2.flip(background, 1)
        background[int(mouse[0]-radius/2):int((mouse[0]+radius/2)),int(mouse[1]-radius/2):int(mouse[1]+radius/2)] = background[int(mouse[0]-radius/2):int((mouse[0]+radius/2)),int(mouse[1]-radius/2):int(mouse[1]+radius/2)]+(sign*1)
        background=cv2.resize(background, (self.win_width,self.win_height), interpolation=cv2.INTER_LANCZOS4)
        if not map:
            self.edit=cv2.flip(background, 1)
            self.edit=cv2.rotate(self.edit, cv2.ROTATE_90_COUNTERCLOCKWISE)
            background = ImageOps.grayscale(Image.fromarray(background))
            background = np.asarray(background)[..., np.newaxis]
            background = np.repeat(background, 3, 2)
        else:
            self.pedit=cv2.flip(background, 1)
            self.pedit=background
        background = pg.surfarray.make_surface(background)
        return background
    
    def full_course(self):
        self.pic = np.where(np.logical_or((np.asarray(self.t_pic.convert('RGB'))==[8,31,130]),(np.asarray(self.t_pic.convert('RGB'))==[55,90,220])), [0,0,0], [100,100,100])
        background = self.voronoi_province_map()
        self.color_maps()
        self.save_maps()
        self.just_def(province=False)
        return background