
import cairo
import shapefile
from math import pi as PI

SHAPE_FILE = 'map_data/nyct2010'
WIDTH = 6000
HEIGHT = 9000

CENTER_LAT = 30

ROT = -0.0805
ROT_RAD = ROT * (2*PI)

SCALE = 2

def main():
    sf = shapefile.Reader(SHAPE_FILE)

    [left, bottom, right, top] = sf.bbox
    box_width = right - left
    box_height = top - bottom
    scale = (HEIGHT / -box_height) * SCALE

    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, WIDTH, HEIGHT)
    ctx = cairo.Context(surface)
    ctx.rectangle(0, 0, WIDTH, HEIGHT)
    ctx.set_source_rgb(1,1,1)
    ctx.fill()
    
    ctx.rotate(ROT_RAD)
    ctx.translate(0, HEIGHT)
    
    ctx.scale(-scale, scale)
    ctx.translate(-left, -bottom)

    ctx.translate(-box_width * 0.56, box_height * -0.4)

    for shape in sf.shapes():
        x, y = shape.points.pop(0)
        ctx.move_to(x, y)

        for x, y in shape.points:
            ctx.line_to(x, y)

        ctx.close_path()
    
        ctx.set_source_rgb(0,0,0)
        ctx.fill()
        #ctx.stroke()
    
    surface.write_to_png('out.png')

if __name__ == '__main__':
    main()

