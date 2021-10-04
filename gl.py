
from obj import Obj, Texture
from lib import *

class Renderer(object):
    def glinit():
        r =  Renderer(1024, 768)

    def __init__(self, width, height):
        self.width = width
        self.height = height
        # Esta variable le da color al punto
        self.current_color = WHITE
        self.current_texture = None # en los triangulos se revisa la textura actual
        self.light = V3(0, 0, 1)
        self.textureC = None

        self.clear()

    def clear(self):
        self.framebuffer = [
            [BLACK for x in range(self.width)]
            for y in range(self.height)
        ]

        # hay que hacer un calculo en todos los pixeles, para ver cual corresponde en su coordenada en z


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

        # Bitmap (se recorre el framebuffer completo, para meter los bytes en un array de 4)
        for y in range(self.height):
            for x in range(self.width):
                try:
                    f.write(self.framebuffer[y][x].toBytes())
                except:
                    pass
        f.close()


 

    def render(self):
        self.write('a.bmp')

        # Se agregara un punto 
    def point(self, x, y, color = None):
        try:

            self.framebuffer[y][x] = color or self.current_color
        except:
            pass

#PARA EL LAB DE TIERRA SE IGNORA LA TEXTURA
    # funcion que recibe 3 vertices y dibuja un triangulo
    def triangle(self):
        A = next(self.active_vertex_array)  # permite acceder al siguiente elemento del array 
        B = next(self.active_vertex_array)
        C = next(self.active_vertex_array)

        if self.current_texture:
            vtA =  next(self.active_vertex_array)
            vtB =  next(self.active_vertex_array)
            vtC =  next(self.active_vertex_array)


        bbox_min, bbox_max = bbox(A, B, C)
        # normalizar un vector u=v/|v|
        normal = norm(cross(
            sub(B, A),
            sub(C, A)
        ))

        intensity = dot(normal, self.light)

        # encontrar el rectangulo mas pequeño
        # se va marcando un punto
        for x in range(bbox_min.x, bbox_max.x + 1):
            for y in range(bbox_min.y, bbox_max.y + 1):
                # se toman las 3 coordenadas de triangulo y el punto P que es (x, y)
                P = V3(x,y)
                w, v, u = barycentric(A, B, C, P)
                # si alguna de las 3 es negativa quiere decir que esta afuera del triangulo
                if w  < 0 or v < 0 or u < 0:
                    continue # todo lo que este despues de continue no se va a ejecutar
                
                # solo si se tiene una textura 
                if self.current_texture:   # cuando se renderizan mas modelos, tiene mas sentido tener current_texture
                    
                    # se va interpolar un triangulo dentro de otro
                    tx = vtA.x * w  + vtB.x * v + vtC.x * u #estas son las coordenadas que corresponden a x, y de este triangulo
                    ty = vtA.y * w + vtB.y * v + vtC.y * u

                    temp_color = self.current_texture.get_color(tx, ty)
                    color1 = temp_color * intensity
                else:
                    color1 = WHITE*intensity
                    
                    # esto es para sacar colores del archivo de textura

                z = A.z * w + B.z * v + C.z * u   # SEGUIR ACA!
                if x < 0 or y < 0:
                    continue
                #  PARA EL LAB 2 se deberia rendizar cada punto que se pinta en la escena 
                if x < len(self.zbuffer) and y < len(self.zbuffer[x]) and z > self.zbuffer[x][y]:
                    self.point(x, y, color1)
                    self.zbuffer[x][y] = z

                    # if x < len(self.zbuffer) and y < len(self.zbuffer[x]) and z > self.zbuffer[x][y]:
                    # self.point(x, y, color)
                    # self.zbuffer[x][y] = z

        # esta es una funcion que reciba un vertice como parametro que se transforma en X y Y
    def transform(self, v, translate=(0, 0, 0), scale=(1, 1, 1)):
       
        return V3(
            round((v[0] + translate[0]) * scale[0]),
            round((v[1] + translate[1]) * scale[1]),
            round((v[2] + translate[2]) * scale[2])
        )

    
    

    # --------------- LINE ---------------

    # Esta funcion es para cargar y renderizar obj
    def load(self, filename, translate=(0, 0, 0), scale=(1, 1, 1)): # ahora a load se le pasa que tanto se quiere que se mueva para los lados y abajo
        # al load se le agregara una textura para cargarla en el modelo 
        
        model = Obj(filename)
        # se tienen que recorrer las caras, agarrar cada uno de los indices y pintar cada vertice
        vertex_buffer_obj = []     # array de vertices

        for face in model. faces:
            for v in range(len(face)):
                vertex =  self.transform(model.vertex[face[v][0] - 1], translate, scale)
                vertex_buffer_obj.append(vertex)

            if self.current_texture:
                # si tiene una textura actual, se pueden meter los vertices de textura de una vez
                for vt in range(len(face)):
                    tvertex =  V3(*model.tvertex[face[vt][1] - 1])
                    vertex_buffer_obj.append(tvertex)

        self.active_vertex_array =  iter(vertex_buffer_obj)

    def draw_array(self, polygon):
        if polygon == 'WIREFRAME':
            self.line()
        elif polygon == 'TRIANGLES':
            # se va recorriendo hasta que se acabe el vertex_array
            try:
                while True:
                    self.triangle()
            except StopIteration:
                print('Done')
            
        

r = Renderer(800, 600)
# r.load('./models/earth1.obj', (800, 600, 0), (0.5, 0.5, 1))
r.current_texture = Texture('./textures/model.bmp')
r.load('./models/model.obj', (1, 1, 1), (300, 300, 300))
r.draw_array('TRIANGLES')

r.write('a.bmp')
