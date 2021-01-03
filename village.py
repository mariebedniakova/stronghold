import pygame
from random import randrange
import pygame
import sys
import os

pygame.init()
FPS = 50
WIDTH = 800
HEIGHT = 800

screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()


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



def terminate():
    pygame.quit()
    sys.exit()


def start_screen():
    intro_text = []
    # созданик экрана, выбор параметров текста и вывод текта

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            elif event.type == pygame.KEYDOWN or \
                    event.type == pygame.MOUSEBUTTONDOWN:
                return  # начинаем игру
        pygame.display.flip()
        clock.tick(FPS)


tile_images = {'Barrak': 'barrak.png',
               'House': 'house.png'}
player_images = {'free_people': 'free_person.jpg'}
all_sprites = pygame.sprite.Group()
player_group = pygame.sprite.Group()
tile_width = tile_height = 200


def correct_coords(x, y, width, hight):
    return 0 <= x < width and 0 <= y < hight


def load_map(filename):
    filename = "data/" + filename
    # читаем уровень, убирая символы перевода строки
    with open(filename, 'r') as mapFile:
        level_map = [line.strip() for line in mapFile]
    max_width = max(map(len, level_map))
    return [list(map(lambda x: x, line)) for line in map(lambda x: x.ljust(max_width, '.'), level_map)]


def load_settings(filename):
    filename = "data/" + filename
    with open(filename, 'r') as settingsFile:
        settings = {}
    return settings


village = load_map('village_plan.txt')
building_group = pygame.sprite.Group()
resources = {'money': 20,
             'free_people': [],
             'warriors': [],
             'food': 0,
             'farmers': []}  # ресурсы игрока для совершения игровых действий
clock = pygame.time.Clock()
GAME_SETTINGS = load_settings('settings.txt')  # табличка



class Building(pygame.sprite.Sprite):  # общий класс для всех построек
    def __init__(self):
        super().__init__(building_group, all_sprites)
        self.symbol = None  # каким символом представлен в матрице
        self.x_pos = None  # в матрице
        self.y_pos = None

    def create(self, x_pos, y_pos):
        if correct_coords(x_pos, y_pos, len(village[0]), len(village)):
            if village[y_pos][x_pos] == '.':
                if self.can_build():
                    village[y_pos][x_pos] = self.symbol
                    self.x_pos, self.y_pos = x_pos, y_pos

                    self.image = pygame.transform.scale(load_image(tile_images[self.get_name()]),
                                                        (tile_width, tile_height))
                    self.rect = self.image.get_rect().move(
                        tile_width * x_pos, tile_height * y_pos)
                    return True

    def can_build(self):  # проверяет, имеются ли ресурсы для постройки
        return True

    def get_name(self):
        return


class Barrack(Building):  # казарма
    def __init__(self):
        super().__init__()
        self.symbol = 'X'
        self.create(randrange(1, len(village[0]) - 1), randrange(1, len(village[0])) - 1)  # не надо создавать вручную

    def make_a_warrior(self):  # делает из незанятого героя воина, может вызываться при клике на картинку
        if resources['money'] and resources['free_people']:
            resources['money'] -= 3
            resources['warriors'].append(resources['free_people'].pop(0))
        return "Недостаточно ресурсов"

    def get_name(self):
        return 'Barrak'


class House(Building):  # жилой дом
    def __init__(self, x_pos, y_pos):
        super().__init__()
        self.symbol = '^'
        self.time = 10 ** 6
        self.money_can_collect = False
        self.create(x_pos, y_pos)

    def create(self, x_pos, y_pos):
        if super().create(x_pos, y_pos):
            resources['money'] -= 20
            for i in range(5):  # строится мгновенно и заселяется 5 героями
                resources['free_people'].append(Hero(self.x_pos, self.y_pos, i * 10))

    def can_build(self):
        return resources['money'] >= 20

    def money(self):  # когда проходит время time можно собрать деньги (вызывется при каждом повторении игрового цикла)
        if clock.get_time() % self.time == 0:
            self.money_can_collect = True

    def collect_money(self):  # сбор денег, вызывается нажатием и работает, если заданное время прошло
        if self.money_can_collect:
            resources['money'] += 5
            self.money_can_collect = False  # деньги собраны

    def get_name(self):
        return 'House'


class Farm(Building):  # ферма
    def __init__(self, x_pos, y_pos):
        super().__init__()
        self.symbol = '*'
        self.time = 10 ** 9
        self.money_can_collect = False
        self.create(x_pos, y_pos)

    def create(self, x_pos, y_pos):
        if super().create(x_pos, y_pos):
            resources['money'] -= 10
            resources['farmers'].append(resources['free_people'].pop(0))  # один герой требуется в фермеры

    def can_build(self):
        return resources['money'] >= 10 and resources['free_people']

    def get_food(self):  # так как тут работает герой, еда собирается независимо от игрока
        resources['food'] += GAME_SETTINGS['food_of_farm']

    def money(self):  # когда проходит время time можно собрать деньги (вызывется при каждом повторении игрового цикла)
        if clock.get_time() % self.time == 0:
            self.money_can_collect = True

    def collect_money(self):  # сбор денег, вызывается нажатием и работает, если заданное время прошло
        if self.money_can_collect:
            resources['money'] += 5
            self.money_can_collect = False

    def get_name(self):
        return Farm


class Hero(pygame.sprite.Sprite):
    def __init__(self, pos_x, pos_y, i=0):
        super().__init__(player_group, all_sprites)
        self.image = pygame.transform.scale(load_image(player_images[self.get_name()]),
                                            (tile_width // 2, tile_height // 2))
        self.rect = self.image.get_rect().move(
            tile_width * (pos_x + 0.5) - i, tile_height * (pos_y + 0.5))
        self.pos = pos_x, pos_y
        self.alive = 100  # уменьшается при уроне, голоде, востанавливается при питании.
        self.time_hunger = 10 ** 7

    def get_name(self):
        return 'free_people'

    def can_live(self):  # вызывется при каждом повторении игрового цикла
        if not self.alive:
            self.die()

    def die(self):  # смерть - удаление из всех ресурсов, плюс групп спрайтов
        del resources[self.get_name()][resources[self.get_name()].index(self)]
        self.kill()

    def eat(self):
        while self.alive < 100 or resources['food']:
            resources['food'] -= 1
            self.alive += 1

    def get_hunger(self):
        if self.alive < 100:
            self.eat()
        if clock.get_time() % self.time_hunger == 0:
            self.alive -= 1
            self.eat()


class Warrior(Hero):
    def __init__(self):
        super().__init__()
        self.time_hunger = 10 ** 5

    def get_name(self):
        return 'warriors'

    def damaged(self, power):
        self.alive -= power
        self.can_live()

    def strike(self, other, power):
        other.damaged(power)


class Farmer(Hero):
    def __init__(self):
        super().__init__()
        self.time = 10 ** 6

    def get_name(self):
        return 'farmer'

fon = pygame.transform.scale(load_image('field.jpg'), (WIDTH, HEIGHT))
screen.blit(fon, (0, 0))
Barrack()
House(0, 0)
print(village)
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    building_group.draw(screen)
    player_group.draw(screen)
    pygame.display.flip()
    clock.tick(FPS)
terminate()
