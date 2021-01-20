#! /usr/bin/env python
"""
@author: cub525
"""
# Known Issues
#  -- Time dimension is really the frame dimension, the longer the frame time the
#     slower the game play

import sys
import random
import pygame as pg

pg.init()

def vector_from_polar(r, phi):
    vector = pg.Vector2()
    vector.from_polar((r, phi))
    vector.y = - vector.y
    return vector

# def collision_normal(sprite1, sprite2):



# Globals for now.
W = 640
H = 480
screen = pg.display.set_mode((W, H))

MAX_BULLETS = 5
MAX_BOMBS = 3
MAX_SHIELDS = 3

BLACK = (0,0,0)
WHITE = (255, 255, 255)
RED = (255,0,0)

# Game States
MENU = 0
PLAYING = 1
GAMEOVER = 2
game_state = MENU


all_sprites_list = pg.sprite.Group()
allied_sprites_list = pg.sprite.Group()
bullets = pg.sprite.Group()
bombs = pg.sprite.Group()
asteroids = pg.sprite.Group()
sheet = pg.image.load("asteroids_sprite_sheet.png")
def asteroid_sprite(sprite_sheet, loc):
    asteroid_sprites = []
    for i in range(0,528,48):
        image = pg.Surface([loc[0]]*2).convert()
        image.blit(sprite_sheet, (0,0), pg.Rect(loc[1],i,loc[0],loc[0]))
        image.set_colorkey(BLACK)
        asteroid_sprites.append(image)

    return asteroid_sprites

images = asteroid_sprite(sheet, (32,0))
L_images = asteroid_sprite(sheet, (48,32))

# TODO create MySprite parent class to cut down on code
class MySprite(pg.sprite.Sprite):
    def __init__(self, size, pos, vel, theta, *groups):
        super().__init__(*groups)
        self.pos = pos
        self.vel = vel
        self.theta = theta
        self.image = pg.Surface([size*2]*2)
        self.rect = self.image.get_rect(center = pos)

    def update(self):
        self.rect.move_ip(self.vel.xy)
        self.rect.x %= W
        self.rect.x %= H

    def coll_detect(self, group):
        for sprite in group:
            pass

    def end_sequence(self):
        self.kill()



class Bullet(pg.sprite.Sprite):
    color = RED
    speed = 10
    length = 10
    width = 3
    def __init__(self, pos, vel, theta, *groups, group = bullets):
        super().__init__(
            all_sprites_list,
            group, *groups)

        # 'standard vars'
        self.pos = pos
        self.vel = vel + vector_from_polar(self.speed, theta)
        self.image = pg.Surface([self.length*2, self.length*2])
        self.rect = self.image.get_rect(center = pos)
        # 'specific vars'
        self.dist = 0
        self.image.fill(BLACK)
        self.image.set_colorkey(BLACK)
        tail = vector_from_polar(self.length, theta)
        pg.draw.line(self.image,
                      self.color,
                      [self.length, self.length],
                      [self.length + tail.x, self.length + tail.y], self.width)
        self.mask = pg.mask.from_surface(self.image)

    def update(self, *args):
        self.rect.move_ip(self.vel.xy)
        self.rect.x %= W
        self.rect.y %= H
        # Class specific code
        self.dist += self.speed
        if self.dist > (W + H) / 3 or pg.sprite.spritecollide(self, asteroids, True, pg.sprite.collide_mask):
            self.end_sequence()

    @classmethod
    def from_ship(cls, ship, *groups):
        projectile = cls(ship.rect.center, ship.vel, ship.theta, *groups)
        return projectile

    def end_sequence(self):
        self.kill()


class Bomb(Bullet):
    color = [75, 75, 75]
    speed = 15
    length = 15
    width = 5
    def __init__(self, pos, vel, theta, *groups):
        super().__init__(pos, vel, theta, *groups, group=bombs)
        self.size = 15
        self.detonate = False
        self.detonate_time = 1

    def end_sequence(self):
        if self.detonate_time == 0:
            self.kill()
        else:
            self.detonate_time -= 1
        self.vel[:] = 0,0
        self.length = 40
        self.image = pg.Surface([self.length*2]*2)
        self.rect = self.image.get_rect(center = self.rect.center)
        self.image.fill(BLACK)
        self.image.set_colorkey(BLACK)
        pg.draw.circle(self.image, [255, 0, 0], [self.length]*2, self.length)
        self.mask = pg.mask.from_surface(self.image)    

class Ship(pg.sprite.Sprite):
    numShields = 0
    size=15
    theta_dot = 10
    speed_dot = 1
    max_speed = 50
    def __init__(self, Color=(255, 255, 255)):
        super().__init__(all_sprites_list)
        self.pos = pg.Vector2(W / 2, H / 2)
        self.vel = pg.Vector2(0,0)
        self.color = Color
        self.theta = 90  # Body Orientation
        self.shield = True
        self.shieldTime = 80
        self.image_ = pg.Surface([self.size*2]*2)
        self.rect = self.image_.get_rect(center = self.pos.xy)
        self.draw_image()
        self.image = pg.transform.rotate(self.image_, self.theta)
        self.bullet_to = 0
        self.bomb_to = 0
        self.mask = pg.mask.from_surface(self.image)

    def draw_image(self):
        # self.image_.fill(BLACK)

        # pg.draw.polygon(self.image_, self.color,
        #                 [(1.75 * self.size, self.size),
        #                   (.5 * self.size, .5 * self.size),
        #                   (.5 * self.size, 1.5 * self.size)])
        self.image_ = pg.image.load("ship.png").convert()
        if self.shield:
            pg.draw.circle(self.image_, (255, 0, 0),
                           [self.size, self.size], self.size, 2)
        self.image_.set_colorkey(BLACK)

    def move(self):
        self.rect.move_ip(self.vel.xy)
        self.rect.y %= H
        self.rect.x %= W

    def left(self):
        self.theta += self.theta_dot
        self.theta %= 360

    def right(self):
        self.theta -= self.theta_dot
        self.theta %= 360

    def forward(self):
        self.vel += vector_from_polar(1, self.theta)
        if self.vel.length_squared() <= self.max_speed**2:
            pass # TODO Implement Max speed
            # TODO Implement Brake

    def update(self, keys):
        # Movement
        if keys[pg.K_w] or keys[pg.K_UP]:
            self.forward()
        if keys[pg.K_a] or keys[pg.K_LEFT]:
            self.left()
        if keys[pg.K_d] or keys[pg.K_RIGHT]:
            self.right()

        self.move()
        loc = self.rect.center
        self.image = pg.transform.rotate(self.image_, self.theta)
        self.rect = self.image.get_rect(center = loc)
        self.mask = pg.mask.from_surface(self.image)
        self.pos = pg.Vector2(self.rect.center)
        # Launch Crews
        if keys[pg.K_SPACE]:  # Shoot
            if self.bullet_to < 0 and len(bullets) <= MAX_BULLETS:
                # Not too many bullets
                Bullet.from_ship(self)
                self.bullet_to = 3
        self.bullet_to -= 1

        if keys[pg.K_LSHIFT] and self.shield == False and self.numShields < 3:
            self.shield = True
            self.numShields += 1
            self.draw_image()
            self.shieldTime = 80

        if self.shieldTime <= 0:
            self.draw_image()
            self.shield = False
            pass
        else:
            self.shieldTime -= 1


        if keys[pg.K_b]:
            if self.bomb_to < 0 and len(bombs) <= MAX_BOMBS:
                Bomb.from_ship(self)
                self.bomb_to = 5
        self.bomb_to -= 1

        if not self.shield:
            self.collision_detect()


    def collision_detect(self):
        for asteroid in asteroids:
            rel = - asteroid.pos + self.pos
            offset = list(map(int, rel))
            if self.mask.overlap_area(asteroid.mask, offset) > 10:
                # return GAMEOVER
                self.kill()
            # else:
            #     return PLAYING

class Asteroid(pg.sprite.Sprite):
    def __init__(self, pos, speed, theta, size=16, Color=(50, 50, 50)):
        super().__init__(all_sprites_list, asteroids)
        self.size = size
        # Same as bullet
        self.pos = pos
        self.vel = vector_from_polar(speed, theta)
        self.color = Color
        # self.image = pg.Surface([size*2]*2)
        self.image = images[random.randint(0, 4)]
        self.image = pg.transform.rotate(self.image, random.randint(0,360))
        self.rect = self.image.get_rect(center=pos)
        # self.image.fill(BLACK)
        self.image.set_colorkey(BLACK)
        # pg.draw.circle(self.image,
        #               self.color,
        #               [size, size],
        #               self.size)
        self.mask = pg.mask.from_surface(self.image)


    def update(self, *args):
        self.pos = pg.Vector2(self.rect.center)
        self.rect.move_ip(self.vel.xy)
        self.rect.y %= H
        self.rect.x %= W

    @classmethod
    def random(cls):
        asteroid = cls(
            pg.Vector2(random.randrange(0, W), random.randrange(0, H)),
            speed=random.randrange(2, 10),
            theta=random.randrange(0, 360))
        return asteroid

    @classmethod
    def random_from_pos(cls, pos):
        asteriod = cls(
            pos,
            speed=random.randrange(2, 10),
            theta=random.randrange(0, 360))
        return asteriod

    def bounce(self):
        for asteroid in asteroids:
            if asteroid != self:
                offset = list(map(int, self.pos - asteroid.pos))
                # dx = self.mask.overlap_area(asteroid.mask, (offset[0] + 1, offset[1])) - mask.overlap_area(othermask, (x - 1, y))
                # dy = mask.overlap_area(asteroid.mask, (x, y + 1)) - mask.overlap_area(othermask, (x, y - 1))

class LargeAsteroid(Asteroid):
    def __init__(self, pos, speed, theta, size=30):
        super().__init__(pos, speed, theta, size=30)
        self.image = L_images[0]
        self.image = pg.transform.rotate(self.image, random.randint(0,360))

    def kill(self, *args):
        self.remove(all_sprites_list, asteroids)
        return Asteroid.random_from_pos(self.pos), Asteroid.random_from_pos(self.pos)


# class AsteroidsGame:
#     def __init__(self):


def main():
    game_state = MENU
    pg.key.set_repeat(10, 10)

    pg.display.set_caption(r"Emmett's Asteroids")
    pg.mouse.set_visible(True)
    clock = pg.time.Clock()

    ship = Ship()



    for _ in range(5):
        asteroids.add(Asteroid.random())
    for _ in range(2):
        asteroids.add(LargeAsteroid.random())
    asteroids.add(Asteroid(pg.Vector2(639,479), speed=0,
                              theta=0, Color=(0, 0, 255)))

    while game_state != GAMEOVER:
        clock.tick(120)
        screen.fill(BLACK)
        keys = pg.key.get_pressed()
        for event in pg.event.get():
            if event.type == pg.MOUSEBUTTONDOWN:
                pos = pg.Vector2(pg.mouse.get_pos())
                asteroids.add(LargeAsteroid(pos, 0, 0, size = 24))
            elif event.type == pg.QUIT or keys[pg.K_ESCAPE]:
                pg.display.quit()
                pg.quit()
                sys.exit()
            elif keys[pg.K_q]:
                game_state = GAMEOVER


        all_sprites_list.draw(screen)

        all_sprites_list.update(keys)
        pg.display.flip()
        pg.time.delay(50)
        if not ship.alive():
            game_state = GAMEOVER

    while game_state == GAMEOVER:
        keys = pg.key.get_pressed()
        for event in pg.event.get():
            if event.type == pg.QUIT or keys[pg.K_ESCAPE]:
                pg.display.quit()
                pg.quit()
                sys.exit()
            elif keys[pg.K_r]:
                main()
        # TODO Create a lose Screen
        screen.fill([0, 0, 0])
        # pg.time.delay(50)
        clock.tick(60)
        pg.display.flip()



if __name__ == '__main__':
    main()

