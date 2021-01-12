import os
import pygame
import sys

pygame.init()
size = 80, 60
cel_size = 10
grass_sprites = pygame.sprite.Group()
screen = pygame.display.set_mode((size[0] * cel_size, size[1] * cel_size))


class Grass(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__(grass_sprites)
        self.image = load_image('grass.png')
        self.image = pygame.transform.scale(self.image, (cel_size, cel_size))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y


def load_image(name, colorkey=None):
    fullname = os.path.join('data', name)
    try:
        image = pygame.image.load(fullname)
    except pygame.error as massage:
        print("Can't load image: ", name)
        raise SystemExit(massage)
    if colorkey is not None:
        image = image.convert()
        if colorkey == -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey)
    else:
        image = image.convert_alpha()
    return image


grass = Grass(0, 0)
screen.fill(pygame.Color("black"))
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    for i in range(0, size[1] * cel_size, cel_size):
        for j in range(0, size[0] * cel_size, cel_size):
            grass = Grass(i, j)
            grass_sprites.draw(screen)
    pygame.display.flip()
    running = False
pygame.quit()
sys.exit()