from obj import Obj, Texture
from lib import *

class Renderer(object):
    def glinit():
        r =  Renderer(1024, 768)

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.current_color = WHITE
        self.current_texture = None 
        self.light = V3(0, 0, 1)
        self.textureC = None

        self.clear()

    def clear(self):
        self.framebuffer = [
            [BLACK for x in range(self.width)]
            for y in range(self.height)
        ]

        self.zbuffer = [
            [-99999 for x in range(self.width)]
            for y in range(self.height)
        ]
        
    def write(self, filename):
        f = open(filename, 'bw')

        # File header (14)
        f.write(char('B'))
        f.write(char('M'))
        f.write(dword(14 + 40 + 3*(self.width*self.height)))
        f.write(dword(0))
        f.write(dword(14 + 40))

        # Info header (40)
        f.write(dword(40))
        f.write(dword(self.width))
        f.write(dword(self.height))
        f.write(word(1))
        f.write(word(24))
        f.write(dword(0))
        f.write(dword(3*(self.width*self.height)))
        f.write(dword(0))
        f.write(dword(0))
        f.write(dword(0))
        f.write(dword(0))

        for y in range(self.height):
            for x in range(self.width):
                try:
                    f.write(self.framebuffer[y][x])
                except:
                    pass
        f.close()

    def render(self):
        self.write('a.bmp')

    def point(self, x, y, color = None):
        try:

            self.framebuffer[y][x] = color or self.current_color
        except:
            pass
    
    def triangle(self, A, B, C, color1= None, textureC=None, intensity=1):
        bbox_min, bbox_max = bbox(A, B, C)

        for x in range(bbox_min.x, bbox_max.x + 1):
            for y in range(bbox_min.y, bbox_max.y + 1):
                P = V3(x,y)
                w, v, u = barycentric(A, B, C, P)
    
                if w  < 0 or v < 0 or u < 0:
                    continue 

                if self.texture:
                    vtA, vtB, vtC = textureC
                   
                    tx = vtA.x * w  + vtB.x * v + vtC.x * u 
                    ty = vtA.y * w + vtB.y * v + vtC.y * u

                    temp_color = self.texture.get_color(tx, ty)
                    b, g, r = [round(c * intensity) if intensity > 0 else 0 for c in temp_color]
                    color1 = color(r, g, b)
                    
                    

                z = A.z * w + B.z * v + C.z * u  
                if x < 0 or y < 0:
                    continue
                if x < len(self.zbuffer) and y < len(self.zbuffer[x]) and z > self.zbuffer[x][y]:
                    self.point(x, y, color1)
                    self.zbuffer[x][y] = z

    def transform(self, v, translate=(0, 0, 0), scale=(1, 1, 1)):
       
        return V3(
            round((v[0] + translate[0]) * scale[0]),
            round((v[1] + translate[1]) * scale[1]),
            round((v[2] + translate[2]) * scale[2])
        )

    #  ALGORITMO DE DIXTRA, VER BRESENHAM ALGORITHM 
    
    def line(self, A, B, color=None):
        x0 = A.x
        x1 = B.x
        y0 = A.y
        y1 = B.y


        dy = abs(y1 - y0)
        dx = abs(x1 - x0)
        
        steep = dy > dx
        if steep:
            x0, y0 = y0, x0
            x1, y1 = y1, x1

        # se voltea
        if x0 > x1:
            x0, x1 = x1, x0
            y0, y1 = y1, y0

        # se reemplatea la pendiente.
        dy = abs(y1 - y0)
        dx = abs(x1 - x0)
    
        offset = 0 # offset = 0 * 2 * dx
        
        threshold = dx # threshold = 0.5 * 2 * dx
        
        y = y0
        points = []

        for x in range(int(x0), int(x1) + 1):
            if steep:
                points.append((y, x, color))
            else:
                points.append((x, y, color))


            offset += 2 * dy # offset += (dy/dx) * 2 * dx
            
            if offset >= threshold:
                y += 1 if y0 < y1 else -1
                threshold += 2 * dx # threshold += 1 * 2 * dx

        for point in points:
            r.point(*point)

    # Esta funcion es para cargar y renderizar obj
    def load(self, filename, translate=(0, 0, 0), scale=(1, 1, 1)): 
      
        model = Obj(filename)
        
        for face in model.faces:
            vcount =  len(face)
            
            if vcount == 3:
                f1 = face[0][0] -1
                f2 = face[1][0] -1
                f3 = face[2][0] -1  

                A = self.transform(model.vertex[f1], translate, scale)
                B = self.transform(model.vertex[f2], translate, scale)
                C = self.transform(model.vertex[f3], translate, scale)

                # normalizar un vector u=v/|v|
                normal = norm(cross(
                    sub(B, A),
                    sub(C, A)
                ))

                intensity = dot(normal, self.light)

                # si no se tiene textura, se colorcara flat shading
                if not self.texture:
                    grey = round(250 * intensity)

                    if grey < 0:
                        continue   

                    self.triangle(A, B, C, color(grey, grey, grey))
                   
                else:
                    f1 = face[0][1] - 1
                    f2 = face[1][1] - 1
                    f3 = face[2][1] - 1
                   
                    
                    vtA = V3(*model.tvertex[f1])
                    vtB = V3(*model.tvertex[f2])
                    vtC = V3(* model.tvertex[f3])

                    self.triangle(A, B, C, textureC = (vtA, vtB, vtC), intensity=intensity)

            elif vcount == 4: # para cuadrados
                f1 = face[0][0] - 1
                f2 = face[1][0] - 1
                f3 = face[2][0] - 1
                f4 = face[3][0] - 1

                A = self.transform(model.vertex[f1], translate, scale)
                B = self.transform(model.vertex[f2], translate, scale)
                C = self.transform(model.vertex[f3], translate, scale)
                D = self.transform(model.vertex[f4], translate, scale)
                normal = norm(cross(
                    sub(B, A),
                    sub(C, A)
                ))
                intensity = dot(normal, self.light)
                grey = round(255 * intensity)

                if not self.texture:

                    grey = round(250 * intensity)
                    if grey < 0:
                        continue
                    self.triangle(A, B, C, color(grey, grey, grey))
                    self.triangle(A, C, D, color(grey, grey, grey))
                else:
                    f1 = face[0][1] - 1
                    f2 = face[1][1] - 1
                    f3 = face[2][1] - 1
                    f4 = face[3][1] - 1

                    vtA = V3(*model.tvertex[f1])
                    vtB = V3(*model.tvertex[f2])
                    vtC = V3(*model.tvertex[f3])
                    vtD = V3(*model.tvertex[f4])

                    self.triangle(A, B, C,textureC = (vtA, vtB, vtC), intensity=intensity)
                    self.triangle(A, C, D,textureC = (vtA, vtC, vtD), intensity=intensity)
    

r = Renderer(800, 600)
# t = Texture('./textures/natsuki.bmp')
# r.texture = t # se tiene que sacar la textura antes del modelo
r.texture = None
# r.load('./models/earth1.obj', (800, 600, 0), (0.5, 0.5, 1))
# r.load('./models/fox.obj', (10, 10, 0), (5, 5, 5))
r.load('./models/chica.obj', (0.5, 0, 0), (500, 500, 300))

r.write('a.bmp')
