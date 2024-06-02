import pygame, sys, math
from const import *
from pygame.math import Vector2

WIDTH, HEIGHT = 300, 200
pygame.init()
screen = pygame.display.set_mode((WIDTH*2, HEIGHT*2),vsync=1)
display = pygame.surface.Surface((WIDTH,HEIGHT))
clock = pygame.time.Clock()
fps = 60
dt = 0 #Delta time
t = 0 #Time in milliseconds

def clampVec2(vec, max):
    if vec.length() == 0:
        return Vector2(0,0)
    l = vec.length()
    f = min(l,max)/l
    return vec*f

def lerp(a, b, t, curve=lambda x:x):
    return a + (b - a) * curve(t)

def loadLevel(level, tileset):
    global object, player
    with open(f'{PATH}Levels/{level}') as txt:
        level = txt.read()
    objects = []
    level = level.split("\n")
    map = []
    for row in level:
        map.append(list(row))
    y=0
    for row in map:
        x=0
        for tile in row:
            if tile == "4":
                Object(Vector2(x*TILESIZE, y*TILESIZE),Vector2(TILESIZE),texture=tileset.tiles[int(tile)],collider=False)
            else:
                Object(Vector2(x*TILESIZE, y*TILESIZE),Vector2(TILESIZE),texture=tileset.tiles[int(tile)],collider=True)
            x+=1
        y+=1
    objects.append(player)

def Draw(camera):
    for object in objects:
        if object.pos.y < player.pos.y:
            object.Draw(camera)
    player.Draw(camera)
    for object in objects:
        if object.pos.y >= player.pos.y:
            object.Draw(camera)
    

class AnimationController:
    def __init__(self, spriteSheet, spriteSize=Vector2(TILESIZE), animation=0, frame=0, frameGap=175):
        #Load all animations
        self.animations = []
        spriteSheet = pygame.image.load(f'{PATH}Assets/{spriteSheet}').convert_alpha()
        for y in range(int(spriteSheet.get_height()/spriteSize.y)):
            newAnim = []
            for x in range(int(spriteSheet.get_width()/spriteSize.x)):
                newFrame = pygame.Surface(spriteSize)
                newFrame.set_colorkey((0,0,0))
                newFrame.blit(spriteSheet,Vector2(-x*spriteSize.x, -y*spriteSize.y))
                newAnim.append(newFrame)
            self.animations.append(newAnim)

        self.animation = animation
        self.frame = frame
        self.frameGap = frameGap
        self.flipX = False
        self.flipY = False

    def Update(self,time,dt):
        self.UpdateFrame(time,dt)
        #Add code for changing animations through class inheritance

    def UpdateFrame(self, time, dt):
        #self.animations[animation number][frame number]
        if (time - dt) // self.frameGap != time // self.frameGap:
            self.frame += 1
            if self.frame+1 > len(self.animations[self.animation]):
                self.frame = 0

    def getFrame(self):
        frame = self.animations.copy()[self.animation][self.frame]
        frame = pygame.transform.flip(frame,self.flipX,self.flipY)
        return frame
    
    def SetAnimation(self, animation):
        if self.animation != animation:
            self.animation = animation
            self.frame = 0

objects = []
class Object:
    def __init__(self, pos, size, velo=Vector2(), texture=(255,0,0), collider=True):
        self.pos = pos
        self.size = size
        self.velo = velo
        if isinstance(texture, str):
            self.texture = pygame.image.load(f'{PATH}Assets/{texture}').convert_alpha()
        else:
            self.texture = texture
        
        self.collider = collider
        objects.append(self)

    def rect(self):
        return pygame.Rect(self.pos.x, self.pos.y, self.size.x, self.size.y)
    
    def center(self):
        return Vector2(self.pos.x+(self.size.x/2),self.pos.y+(self.size.y/2))
    
    def Draw(self, camera):
        if isinstance(self, AnimationController):
            display.blit(self.getFrame(), self.pos-camera.pos)
        elif isinstance(self.texture, tuple):
            pygame.draw.rect(display, self.texture, pygame.Rect(self.pos.x-camera.pos.x,self.pos.y-camera.pos.y,self.size.x,self.size.y))
        elif isinstance(self.texture, pygame.Surface):
            display.blit(self.texture, self.pos-camera.pos)

    def Physics(self, friction, dt):
        if self.collider == True:
            self.velo.x *= 1/(1+(friction*dt))
            self.pos.x += self.velo.x*dt
            for object in objects:
                if object != self and object.rect().colliderect(self.rect()) and object.collider == True:
                    if self.velo.x > 0:
                        self.pos.x = object.pos.x - self.size.x
                    if self.velo.x < 0:
                        self.pos.x = object.pos.x + object.size.x

            self.velo.y *= 1/(1+(friction*dt))
            self.pos.y += self.velo.y*dt
            for object in objects:
                if object != self and object.rect().colliderect(self.rect()) and object.collider == True:
                    if self.velo.y > 0:
                        self.pos.y = object.pos.y - self.size.y
                    if self.velo.y < 0:
                        self.pos.y = object.pos.y + object.size.y

class Player(Object, AnimationController):
    def __init__(self, pos, size, spriteSheet, velo=Vector2(), texture=(255,0,0), animation=0, frame=0, frameGap=175, spriteSize=Vector2(TILESIZE)):
        Object.__init__(self,pos,size,velo,texture)
        AnimationController.__init__(self,spriteSheet,spriteSize,animation,frame,frameGap)

    def Update(self,time,dt):
        self.UpdateFrame(time,dt)
        if self.velo.x > 0:
            self.flipX = False
        if self.velo.x < 0:
            self.flipX = True
        if self.velo.length() < 0.01:
            self.SetAnimation(0)
        elif abs(self.velo.x) > abs(self.velo.y):
            self.SetAnimation(1)
        elif self.velo.y < 0:
            self.SetAnimation(3)
        elif self.velo.y > 0:
            self.SetAnimation(2)

class Camera:
    def __init__(self, pos, focus, lerp=lambda x:x, speed=0.7):
        self.pos = pos
        self.focus = focus
        self.lerp = lerp
        self.speed = speed

    def Update(self, dt):
        self.pos.x = lerp(self.pos.x, self.focus.center().x+(self.focus.velo.x*WIDTH)-(WIDTH/2), self.speed*(dt/1000), self.lerp)
        self.pos.y = lerp(self.pos.y, self.focus.center().y+(self.focus.velo.y*HEIGHT)-(HEIGHT/2), (self.speed*(dt/1000))*(WIDTH/HEIGHT), self.lerp)

class TileSet:
    def __init__(self, set, tileSize=TILESIZE):
        self.tiles = []
        set = pygame.image.load(f'{PATH}Assets/{set}').convert_alpha()
        for i in range(int(set.get_width()/tileSize)):
            surf = pygame.Surface(Vector2(tileSize))
            surf.set_colorkey((0,0,0))
            surf.blit(set,Vector2(-i*tileSize,0))
            self.tiles.append(surf)

tileset = TileSet("tileset.png")  

#wall = Object(Vector2(16,16),Vector2(16,16),texture=tileset.tiles[0])

player = Player(Vector2(16,16),Vector2(16,16),"player.png")

camera = Camera(Vector2(0,0),player)#lambda x:-(x**2)+(x*2)

loadLevel("1.txt",tileset)

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    keys = pygame.key.get_pressed()
    if keys[pygame.K_UP]:
        player.velo.y = -0.25
    if keys[pygame.K_DOWN]:
        player.velo.y = 0.25
    if keys[pygame.K_LEFT]:
        player.velo.x = -0.25
    if keys[pygame.K_RIGHT]:
        player.velo.x = 0.25
    player.velo = clampVec2(player.velo, 0.25)
    
    
    camera.Update(dt)
    display.fill((255,255,255))
    for object in objects:
        object.Physics(0.1, dt)
        if isinstance(object, AnimationController):
            object.Update(t,dt)
    Draw(camera)

    screen.blit(pygame.transform.scale_by(display,2),(0,0))
    pygame.display.update()
    dt = clock.tick(fps)
    t += dt