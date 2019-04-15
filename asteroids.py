#! /usr/bin/env python 

# Known Issues
#  -- If you hold down a key (say left arrow) and then push another (say space) 
#     the repeat function stops for the key you holding down (seems like a bug
#     in pygame. A work around would be to also check the keyboard state after
#     parsing the event queue 
#  -- Time dimension is really the frame dimension, the longer the frame time the 
#     slower the game play 
#  -- Should have extended the sprite object for all of the game object (apparently
#     it has all the move, draw, collision detection algorithms built in.)

import sys
import random
import math
import pygame as pg

pg.init()


# Globals for now.
w = 640;
h = 480;
MAX_BULLETS = 5;
MAX_BOMBS = 3;
MAX_SHIELDS = 3;

# Game States
MENU = 0
PLAYING = 1
GAMEOVER = 2   


class Bullet:
   def __init__(self,x,y,vx,vy,theta):
      self.x=x
      self.y=y
      self.vx=vx
      self.vy=vy
      self.theta=theta
      self.color=[255,0,0];
      self.speed=10
      self.dist=0;
      self.length=10;
      self.tailx =self.x+self.length*math.sin(self.theta-math.pi)
      self.taily =self.y-self.length*math.cos(self.theta-math.pi)
   def move(self):
      self.x+=self.speed*math.sin(self.theta)+self.vx
      self.y+=-self.speed*math.cos(self.theta)+self.vy
      self.dist+=self.speed
      self.x %= w
      self.y %= h
      self.tailx =self.x+self.length*math.sin(self.theta-math.pi) 
      self.taily =self.y-self.length*math.cos(self.theta-math.pi)

class Boomerang:
   def __init__(self,x,y,vx,vy,theta):
      self.x=x
      self.y=y
      self.vx=vx
      self.vy=vy
      self.theta=theta
      self.color=[0,0,255];
      self.speed=15
      self.dist=0;
      self.length=10;
      self.tailx =self.x+self.length*math.sin(self.theta-math.pi)
      self.taily =self.y-self.length*math.cos(self.theta-math.pi)
   def move(self):
      self.x+=self.speed*math.sin(self.theta)+self.vx
      self.y+=-self.speed*math.cos(self.theta)+self.vy
      self.dist+=self.speed
      self.x %= w
      self.y %= h
      self.tailx =self.x+self.length*math.sin(self.theta-math.pi) 
      self.taily =self.y-self.length*math.cos(self.theta-math.pi)

class Bomb:
   def __init__(self,x,y,vx,vy,theta):
      self.x=x
      self.y=y
      self.vx=vx
      self.vy=vy
      self.theta=theta
      self.color=[75,75,75];
      self.speed=15
      self.dist=0;
      self.length=15;
      self.tailx =self.x+self.length*math.sin(self.theta-math.pi)
      self.taily =self.y-self.length*math.cos(self.theta-math.pi)
      self.detonate = False
      self.size = 15
   def move(self):
      self.x+=self.speed*math.sin(self.theta)+self.vx
      self.y+=-self.speed*math.cos(self.theta)+self.vy
      self.dist+=self.speed
      self.x %= w
      self.y %= h
      self.tailx =self.x+self.length*math.sin(self.theta-math.pi) 
      self.taily =self.y-self.length*math.cos(self.theta-math.pi)
   def set_detonate(self,det):
      self.detonate = det
      self.size = 5*15
   def dirtyCollDetect(self,asteroid):
      dist=self.distance(asteroid.x,asteroid.y);
      return dist <= (self.size)
   def distance(self,x,y):
      return math.sqrt((self.x-x)**2+(self.y-y)**2)


class Ship:
   def __init__(self,size=15,Color=(255,255,255)):
      self.x=w/2;
      self.y=h/2;
      self.vx=0;
      self.vy=0;
      self.theta=0; #Body Orientation
      self.color=Color;
      self.size=size;
      self.theta_dot=0.2
      self.speed_dot=1
      self.base=size;
      self.height=1.5*size;
      self.max_speed=50;
      self.shield=True
      self.shieldTime=2*40
   def move(self):
      self.y+=self.vy
      self.x+=self.vx
      self.y=self.y % h
      self.x=self.x % w
      self.shieldTime-=1
      if self.shieldTime <= 0:
         self.shield = False
   def left(self):
      self.theta-=self.theta_dot
   def right(self):
      self.theta+=self.theta_dot
   def forward(self):
      self.vx+=math.sin(self.theta)
      self.vy+=-math.cos(self.theta)
      self.speed=math.sqrt(self.vx**2+self.vy**2)
      if self.speed > self.max_speed:
         None #no implementation yet
   def distance(self,x,y):
      return math.sqrt((self.x-x)**2+(self.y-y)**2)
   def vertices(self):
      #There is probably some built-in type that would make this easier.
      #This isn't any of the definitions of the center of triangle, close enough for today
      vself=[[-self.base*0.5,self.height*0.5],[self.base*0.5,self.height*0.5],[0,-self.height*0.5]]
      vrot=self.rot(vself);
      v=self.bias(vrot);
      return v
   def rot(self,v):
      vrot=[];
      for i in range(0,3):
         vrot.append([math.cos(self.theta)*v[i][0] - math.sin(self.theta)*v[i][1],
         math.sin(self.theta)*v[i][0] + math.cos(self.theta)*v[i][1] ])
      return vrot
   def bias(self,v):
      vbias=v
      for i in range(0,3):
         vbias[i][0]+=self.x
         vbias[i][1]+=self.y
      return v
   def dirtyCollDetect(self,asteroid):
      if self.shield:
         return False
      else:
         dist=self.distance(asteroid.x,asteroid.y);
         return dist <= (asteroid.size+self.size/2.0)


class Asteroid(object):
   def __init__(self,x,y,speed,theta,size=15,Color=(50,50,50)):
      self.x = int(x)
      self.y = int(y)
      self.speed = speed
      self.theta = theta
      self.size = int(size)
      self.color = Color
   def move(self):
      self.y+=self.speed*math.cos(self.theta)
      self.x+=self.speed*math.sin(self.theta)
      self.y=self.y % h
      self.x=self.x % w
   def distance(self,x,y):
      return math.sqrt((self.x-x)**2+(self.y-y)**2)
# Only reliable for explosions, not inelastic collisions
   def dirtyCollDetect(self,bullet):
      dist=self.distance(bullet.x,bullet.y);
      return dist <= (self.size)

class L_Asteroid(Asteroid):
   def __init__(self,x,y,speed,theta):
      super(L_Asteroid, self).__init__(x,y,speed,theta)
      self.size = 30;
   def split(self):
      return [Asteroid(self.x,self.y,speed=random.randrange(1,10),theta=random.randrange(0,360)),
              Asteroid(self.x,self.y,speed=random.randrange(1,10),theta=random.randrange(0,360))]

def GetInput():
    keystate = pg.key.get_pressed()
    for event in pg.event.get():
        if event.type == pg.QUIT or keystate[pg.K_ESCAPE]:
            pg.display.quit()
            pg.quit()
            sys.exit()

def main():
   gameState = MENU
   # This causes holding a key down to cause repeated keydown events in the gueue,
   # the 2nd event is after argv[1] milliseconds and the nth delay is after argv[2]
   # milliseconds
   numShields = 0;
   pg.key.set_repeat(10, 10)
   screen = pg.display.set_mode((w,h))
   pg.display.set_caption(r"Emmett's Asteroids")
   pg.mouse.set_visible(1)
   clock = pg.time.Clock()
 
   ship=Ship();
   bullets=[];
   bombs=[]
   Asteroids =[];

   for each in range(0,5):
      Asteroids.append(Asteroid(random.randrange(0,w),random.randrange(0,h),speed=random.randrange(1,10),theta=random.randrange(0,360)))
   for each in range(0,2):
      Asteroids.append(L_Asteroid(random.randrange(0,w),random.randrange(0,h),speed=random.randrange(1,5),theta=random.randrange(0,360)))
   Asteroids.append(Asteroid(x=639,y=479,speed=0,theta=0,Color=(0,0,255)))
   
   while (not (gameState == GAMEOVER)):
      GetInput()
      clock.tick(120)
      screen.fill([0,0,0]);
      for event in pg.event.get():
         if event.type==pg.QUIT:
            sys.exit()
         if event.type==(pg.MOUSEBUTTONDOWN):
            pos=pg.mouse.get_pos()
            Asteroids.append(L_Asteroid(pos[0],pos[1],speed=random.randrange(1,10),theta=random.randrange(0,360)))
      keys = pg.key.get_pressed()
      if keys[pg.K_UP]:
         ship.forward()
      if keys[pg.K_LEFT]:
         ship.left()
      if keys[pg.K_RIGHT]:
         ship.right()
      if keys[pg.K_SPACE]: #Shoot
         if len(bullets) <= MAX_BULLETS: # Not too many bullets
            bullets.append(Bullet(ship.x,ship.y,ship.vx,ship.vy,ship.theta))
      if keys[pg.K_s]: #shields
         if numShields < MAX_SHIELDS and not ship.shield:
          numShields=numShields+1  
     # ship.shield=True
      #ship.shieldTime=2

      if keys[pg.K_b]: #bomb
         if len(bombs) < MAX_BOMBS: # Not too many bombs
            bombs.append(Bomb(ship.x,ship.y,ship.vx,ship.vy,ship.theta))

# Draw, move and detect collisions for asteroids
      for asteroid in Asteroids:
         asteroid.move();
         if ship.dirtyCollDetect(asteroid) or gameState == GAMEOVER:
            gameState = GAMEOVER
         for b in bullets:
            if asteroid.dirtyCollDetect(b):
               Asteroids.remove(asteroid)
               if isinstance(asteroid,L_Asteroid):
                  Asteroids.extend(asteroid.split()) 
               bullets.remove(b)
               break
         for b in bombs:
            if b.dirtyCollDetect(asteroid):
               Asteroids.remove(asteroid)
               b.set_detonate(True)
               break
         pg.draw.circle(screen,asteroid.color,[int(asteroid.x),int(asteroid.y)],asteroid.size);

# draw and move bullets      
      for b in bullets:
         b.move()
         if b.dist > (w+h)/3:
            bullets.remove(b)
         pg.draw.line(screen, b.color, [b.x,b.y], [b.tailx,b.taily], 3)

# draw and move bombs      
      for b in bombs:
         b.move()
         if b.dist > (w+h)/3:
            b.set_detonate(True)
         if b.detonate:
            pg.draw.circle(screen,[255,0,0],[int(b.x),int(b.y)],b.size)
            for asteroid in Asteroids:
               if b.dirtyCollDetect(asteroid):
                  Asteroids.remove(asteroid)
            bombs.remove(b)
         else:
            pg.draw.line(screen, b.color, [b.x,b.y], [b.tailx,b.taily], 6)
            if b.color == [75,75,75]:
               b.color = [255,0,0]
            else:
               b.color = [75,75,75]

# Draw and move ship       
      ship.move();
      pg.draw.polygon(screen, ship.color, ship.vertices() )
      if ship.shield:
         pg.draw.circle(screen,(255,0,0),[int(ship.x),int(ship.y)],ship.size, 2);

# Update the screen and wait for the next frame
      pg.display.flip();
      pg.time.delay(50)
      
   # End while(gameOver)
   
   #Blank the screen and do nothing
   screen.fill([0,0,0]);
   pg.display.flip();


if __name__ == '__main__': main()



























