
import cairo
import shapefile
from rtree.index import Index
from math import pi as PI
from shapely.geometry.point import Point
from shapely.geometry.polygon import Polygon

SHAPE_FILE = 'map_data/nyct2010'
WIDTH = 600
HEIGHT = 900

BOX_HEIGHT = 20
BOX_WIDTH = 30

ROT = -0.0805
ROT_RAD = ROT * (2*PI)

SCALE = 2
X_TRANSLATE_FACTOR = -0.58
Y_TRANSLATE_FACTOR = -0.4

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
        for index, shape in enumerate(self.shapes):
            self.index.insert(index, shape.bbox)

    def get_shape_at_point(self, (x, y)):
        candidates = self.index.intersection((x, y, x, y))
        for candidate in candidates:
            shape = self.shapes[candidate]
            if Polygon(shape.points).contains(Point(x, y)):
                return True
        return False

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
            proj_point = projection.device_to_user(x, y)
            ctx.rectangle(x, y, BOX_WIDTH, BOX_HEIGHT)
            if polystore.get_shape_at_point(proj_point):
                ctx.set_source_rgb(1,0,0)
            else:
                ctx.set_source_rgb(0,1,0)
            ctx.fill()


            x = x + BOX_WIDTH
        y = y + BOX_HEIGHT
    
    surface.write_to_png('out.png')

if __name__ == '__main__':
    main()

