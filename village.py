import pygame
from random import randrange
import pygame
import sys
import os
import csv

pygame.init()
FPS = 50
WIDTH = 1000
HEIGHT = 800

screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
tick_count = 0


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
               'House': 'house.png',
               'Farm': 'Farm.png'}
player_images = {'free_people': 'free_person.png',
                 'farmer': 'farmer.png',
                 'warriors': 'warrior.png'}
all_sprites = pygame.sprite.Group()
player_group = pygame.sprite.Group()
tile_width = tile_height = 200
battle_begin = False


def correct_coords(x, y, width, hight):
    return 0 <= x < width and 0 <= y < hight


def convert_coords(x, y):
    if correct_coords(x, y, WIDTH - 200, HEIGHT):
        return y // tile_height, x // tile_width


def load_map(filename):
    filename = "data/" + filename
    # читаем уровень, убирая символы перевода строки
    with open(filename, 'r') as mapFile:
        level_map = [line.strip() for line in mapFile]
    max_width = max(map(len, level_map))
    return [list(map(lambda x: x, line)) for line in map(lambda x: x.ljust(max_width, '.'), level_map)]


def load_settings(filename):
    settings = []
    filename = "data/" + filename
    with open(filename, encoding="utf8") as settingsFile:
        reader = csv.DictReader(settingsFile, delimiter=';', quotechar='"')
        for el in reader:
            settings.append(el)
    return settings[0]


village = load_map('village_plan.txt')
building_group = pygame.sprite.Group()
resources = {'money': 100000,
             'free_people': [],
             'warriors': [],
             'food': 0,
             'farmers': []}  # ресурсы игрока для совершения игровых действий
clock = pygame.time.Clock()
GAME_SETTINGS = load_settings('settings.csv')  # табличка


class Collector(pygame.sprite.Sprite):
    def __init__(self, coords):
        super().__init__(all_sprites)
        self.x_pos = coords[1] * tile_width + 100  # на поле
        self.y_pos = coords[0] * tile_height
        self.image = pygame.transform.scale(load_image('collector.png'),
                                            (tile_width // 4, tile_height // 4))
        self.rect = self.image.get_rect().move(self.x_pos, self.y_pos)


class Building(pygame.sprite.Sprite):  # общий класс для всех построек
    def __init__(self):
        super().__init__(building_group, all_sprites)
        self.symbol = None  # каким символом представлен в матрице
        self.x_pos = None  # в матрице
        self.y_pos = None
        self.money = None

    def get_coords(self):
        return self.x_pos, self.y_pos

    def create(self, x_pos, y_pos):
        if correct_coords(x_pos, y_pos, len(village[0]), len(village)):
            if village[x_pos][y_pos] == '.':
                if self.can_build():
                    village[x_pos][y_pos] = self.symbol
                    self.x_pos, self.y_pos = x_pos, y_pos

                    self.image = pygame.transform.scale(load_image(tile_images[self.get_name()]),
                                                        (tile_width, tile_height))
                    self.rect = self.image.get_rect().move(
                        tile_width * y_pos, tile_height * x_pos)
                    return 'OK'
                return 'Недостаточно средств'
            return 'Невозможно построить здесь'

    def can_build(self):  # проверяет, имеются ли ресурсы для постройки
        return True

    def get_name(self):
        return

    def can_collect(
            self):  # когда проходит время time можно собрать деньги (вызывется при каждом повторении игрового цикла)
        if tick_count % self.time == 0:
            self.money_can_collect = True
        return self.money_can_collect

    def collect_money(self):  # сбор денег, вызывается нажатием и работает, если заданное время прошло
        if self.money_can_collect:
            resources['money'] += self.money
            self.money_can_collect = False  # деньги собраны


class Barrack(Building):  # казарма
    def __init__(self):
        super().__init__()
        self.symbol = 'X'
        self.create(randrange(1, len(village[0]) - 1), randrange(1, len(village[0])) - 1)  # не надо создавать вручную
        self.time = int(GAME_SETTINGS['time_of_barrak'])
        self.money = int(GAME_SETTINGS['money_of_barrak'])

    def make_a_warrior(self):  # делает из незанятого героя воина, может вызываться при клике на картинку
        if resources['money'] and resources['free_people']:
            resources['money'] -= 3
            resources['free_people'][0].kill()  # один герой требуется в фермеры
            del resources['free_people'][0]
            resources['warriors'].append(Warrior(self.x_pos, self.y_pos))
            return 'OK'
        return "Недостаточно ресурсов"

    def get_name(self):
        return 'Barrak'


class House(Building):  # жилой дом
    def __init__(self, x_pos, y_pos):
        super().__init__()
        self.symbol = '^'
        self.time = int(GAME_SETTINGS['time_of_house'])
        self.money = int(GAME_SETTINGS['money_of_house'])
        self.money_can_collect = False
        self.create(x_pos, y_pos)

    def create(self, x_pos, y_pos):
        can_create = super().create(x_pos, y_pos)
        if can_create == 'OK':
            resources['money'] -= 20
            for i in range(5):  # строится мгновенно и заселяется 5 героями
                resources['free_people'].append(Hero(self.x_pos, self.y_pos))
            return 'OK'
        else:
            return can_create

    def can_build(self):
        return resources['money'] >= 20

    def get_name(self):
        return 'House'


class ControlPanel():  # панель управления
    def __init__(self):
        self.title_font = pygame.font.Font(pygame.font.match_font('goudyoldstyleполужирный'), 30)
        self.text_font = pygame.font.Font(pygame.font.match_font('goudyoldstyle'), 20)
        self.draw()

    def draw(self):
        screen.fill((161, 150, 114), pygame.Rect(810, 10, 180, 780))
        text = self.title_font.render("resources", True, (61, 82, 20))
        text_x = 900 - text.get_width() // 2
        text_y = 30 - text.get_height() // 2
        screen.blit(text, (text_x, text_y))
        k = 0
        for resource in resources:
            if not str(resources[resource]).isdigit():
                value = len(resources[resource])
            else:
                value = resources[resource]
            text = self.text_font.render(f'{resource}:  {value}', True, (61, 82, 20))
            text_x = 900 - text.get_width() // 2
            text_y = 60 + 25 * k - text.get_height() // 2
            screen.blit(text, (text_x, text_y))
            k += 1

    def update(self):
        self.draw()


class Farm(Building):  # ферма
    def __init__(self, x_pos, y_pos):
        super().__init__()
        self.symbol = '*'
        self.time = int(GAME_SETTINGS['time_of_farm'])
        self.money = int(GAME_SETTINGS['money_of_farm'])
        self.money_can_collect = False
        self.create(x_pos, y_pos)

    def create(self, x_pos, y_pos):
        can_create = super().create(x_pos, y_pos)
        if can_create == 'OK':
            resources['money'] -= 10
            resources['free_people'][0].kill()  # один герой требуется в фермеры
            del resources['free_people'][0]
            resources['farmers'].append(Farmer(self.x_pos, self.y_pos))
            return 'OK'
        else:
            return can_create

    def can_build(self):
        return resources['money'] >= 10 and resources['free_people']

    def get_food(self):  # так как тут работает герой, еда собирается независимо от игрока
        if tick_count % int(GAME_SETTINGS['time_of_food']) == 0:
            resources['food'] += int(GAME_SETTINGS['food_of_farm'])

    def get_name(self):
        return 'Farm'


class Hero(pygame.sprite.Sprite):
    def __init__(self, pos_y, pos_x):
        super().__init__(player_group, all_sprites)
        self.image = pygame.transform.scale(load_image(player_images[self.get_name()]),
                                            (tile_width // 2, tile_height // 2))
        self.rect = self.image.get_rect().move(randrange(tile_width * pos_x + 70, tile_width * pos_x + 150),
                                               randrange(tile_height * pos_y + 70, tile_height * pos_y + 100))
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
    def __init__(self, pos_x, pos_y):
        super().__init__(pos_x, pos_y)
        self.time_hunger = 10 ** 5

    def get_name(self):
        return 'warriors'

    def damaged(self, power):
        self.alive -= power
        self.can_live()

    def strike(self, other, power):
        other.damaged(power)


class AnimatedWarrior(Warrior):
    pass


class Farmer(Hero):
    def __init__(self, pos_x, pos_y):
        super().__init__(pos_x, pos_y)
        self.time = 10 ** 6

    def get_name(self):
        return 'farmer'



# village_screen = pygame.Surface(screen.get_size())
# battlefield_screen = pygame.Surface(screen.get_size())
# screen.blit(village_screen, (0, 0))
place = 'village'
fon_image = pygame.transform.scale(load_image('field.jpg'), (WIDTH, HEIGHT))
fon = pygame.sprite.Sprite(all_sprites)
fon.image = fon_image
fon.rect = fon_image.get_rect().move(0, 0)
print(pygame.font.get_fonts())
barrack = Barrack()
control_panel = ControlPanel()
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN and convert_coords(*event.pos) == barrack.get_coords()\
                and event.button == 3:
            barrack.make_a_warrior()
        elif event.type == pygame.MOUSEBUTTONDOWN and \
                village[convert_coords(*event.pos)[0]][convert_coords(*event.pos)[1]] != '.' and place == 'village':
            house = list(filter(lambda x: x.get_coords() == convert_coords(*event.pos), building_group))[0]
            house.collect_money()
            for sprite in all_sprites:
                if sprite.__class__.__name__ == 'Collector':
                    sprite.kill()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and place == 'village':
            House(*convert_coords(*event.pos))
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3 and place == 'village':
            Farm(*convert_coords(*event.pos))
        elif battle_begin and event.key == pygame.K_SPACE:
            # screen.blit(battlefield_screen, (0, 0))
            place = 'battlefield'
            # дописать
    for building in building_group:
        if building.can_collect():
            Collector(building.get_coords())
        if building.__class__.__name__ == 'Farm':
            building.get_food()

    all_sprites.draw(screen)
    control_panel.update()
    pygame.display.flip()
    clock.tick(FPS)
    tick_count += 1
terminate()
