
import cairo
import shapefile
import csv
from random import random
from rtree.index import Index
from math import pi as PI
from shapely.geometry.point import Point
from shapely.geometry.polygon import Polygon
from glob import glob

SHAPE_FILE = 'map_data/nyct2010'
DATA_FILE = 'acs_data/ACS_10_5YR_B05006_with_ann.csv'
FLAG_FILES = 'flags-png/*.png'
WIDTH = 6000
HEIGHT = 9000

BOX_HEIGHT = 10
BOX_WIDTH = 14 # approximation

ROT = -0.0805
ROT_RAD = ROT * (2*PI)

SCALE = 2
X_TRANSLATE_FACTOR = -0.58
Y_TRANSLATE_FACTOR = -0.4

TRACTMAP = {
    '36061': '1', # Manhattan / New York County
    '36005': '2', # Bronx / Bronx County
    '36047': '3', # Brooklyn / Kings County
    '36081': '4', # Queens / Queens County
    '36085': '5'  # Staten Island / Richmond County
}

class FlagImages(object):
    def __init__(self):
        self.flags = dict()
        for fn in glob(FLAG_FILES):
            img = cairo.ImageSurface.create_from_png(fn)
            fn = fn.split('/')[1].split('.')[0]
            self.flags[fn] = img

    def get_flag(self, country):
        if country in self.flags:
            return self.flags[country]

def country_code(country):
    if country[:5] == 'Other':
        return
    if country[-1] == ':':
        return
    if country[-6:] == 'n.e.c.':
        return
    if country[:5] == 'West ':
        return
    country = country.split(',')[0]
    country = country.split(' (')[0]
    return country.lower().replace(' ','_').replace('.','')

def map_tract(tract_id):
    county_id, county_tract = tract_id[:5], tract_id[5:]
    if county_id in TRACTMAP:
        return '%s%s' % (TRACTMAP[county_id], county_tract)

class BirthData(object):
    def __init__(self, reader):
        self.data = dict()
        reader.next()
        country_indices = reader.next()

        for tract in reader:
            tract_id = map_tract(tract[1])
            if tract_id:
                total = 0
                origins = []
                for country, value in zip(country_indices, tract):
                    measure = country.split(';')[0]
                    if measure != 'Estimate' or value == '0':
                        continue
                    value = int(value)
                    country = country.split(' - ')[-1]
                    code = country_code(country)
                    if code:
                        origins.append((code, value))
                        total += value
                if total > 0:
                    self.data[tract_id] = [(country, val / float(total)) for country, val in origins]

    def pick_one(self, tract_id):
        num = random()
        tot = 0
        if tract_id not in self.data:
            return
        countries = self.data[tract_id]
        for (country, weight) in countries:
            tot += weight
            if tot > num:
                return country

def get_projection(sf, surface):
    [left, bottom, right, top] = sf.bbox
    box_width = right - left
    box_height = top - bottom
    scale = (HEIGHT / -box_height) * SCALE

    ctx = cairo.Context(surface)
    
    ctx.rotate(ROT_RAD)
    ctx.translate(0, HEIGHT)
    
    ctx.scale(-scale, scale)
    ctx.translate(-left, -bottom)

    ctx.translate(box_width * X_TRANSLATE_FACTOR, box_height * Y_TRANSLATE_FACTOR)

    ctx.set_line_width(100)
    return ctx

class PolyStore(object):
    def __init__(self):
        self.index = Index()

    def load_from_shapefile(self, sf):
        self.shapes = sf.shapes()
        self.records = sf.records()
        for index, shape in enumerate(self.shapes):
            self.index.insert(index, shape.bbox)

    def get_shape_at_point(self, (x, y)):
        candidates = self.index.intersection((x, y, x, y))
        for candidate in candidates:
            shape = self.shapes[candidate]
            if Polygon(shape.points).contains(Point(x, y)):
                return self.records[candidate]
        return None

def draw_projection(sf, ctx):
    for shape in sf.shapes():
        x, y = shape.points.pop(0)
        ctx.move_to(x, y)

        for x, y in shape.points:
            ctx.line_to(x, y)

        ctx.close_path()
    
        ctx.set_source_rgb(0,0,0)
        ctx.fill_preserve()
        ctx.set_source_rgb(1,1,1)
        ctx.stroke()

def main():
    flags = FlagImages()
    bd = BirthData(csv.reader(file(DATA_FILE)))

    sf = shapefile.Reader(SHAPE_FILE)
    polystore = PolyStore()
    polystore.load_from_shapefile(sf)

    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, WIDTH, HEIGHT)
    ctx = cairo.Context(surface)

    ctx.rectangle(0, 0, WIDTH, HEIGHT)
    ctx.set_source_rgb(1,1,1)
    ctx.fill()

    projection = get_projection(sf, surface)

    y = 0
    while y < HEIGHT:
        print y
        x = 0
        while x < WIDTH:
            proj_point = projection.device_to_user(x+BOX_WIDTH/2, y+BOX_HEIGHT/2)

            record = polystore.get_shape_at_point(proj_point)
            if record:
                tract_id = record[4]
                country = bd.pick_one(tract_id)
                if country:
                    img = flags.get_flag(country)
                    if img:
                        ctx.set_source_surface(img, x, y)
                        ctx.paint()
                        x = x + img.get_width()
                        continue
                    else:
                        pass
                        #ctx.rectangle(x, y, BOX_WIDTH, BOX_HEIGHT)
                        #ctx.set_source_rgb(1,0,0)
                else:
                    pass
                    #ctx.rectangle(x, y, BOX_WIDTH, BOX_HEIGHT)
                    #ctx.set_source_rgb(0,0,1)
            else:
                pass
                #ctx.rectangle(x, y, BOX_WIDTH, BOX_HEIGHT)
                #ctx.set_source_rgb(0,1,0)
            #ctx.fill()


            x = x + BOX_WIDTH
        y = y + BOX_HEIGHT
    
    surface.write_to_png('out.png')

if __name__ == '__main__':
    main()

