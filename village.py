import pygame
from random import randrange

# TODO картинки

def correct_coords(x, y, width, hight):
    return 0 <= x < width and 0 <= y < hight


def load_map(filename):
    filename = "data/" + filename
    # читаем уровень, убирая символы перевода строки
    with open(filename, 'r') as mapFile:
        level_map = [line.strip().split('') for line in mapFile]
    max_width = max(map(len, level_map))
    return list(map(lambda x: x.ljust(max_width, '0'), level_map))


village = load_map('village_plan.txt')
building_group = pygame.sprite.Group()
resources = {'money': 0,
             'free_people': [],
             'warriors': [],
             'food': 0,
             'farmers': []}  # ресурсы игрока для совершения игровых действий
clock = pygame.time.Clock()


class Building(pygame.sprite.Sprite):  # общий класс для всех построек
    def __init__(self):
        super.__init__(building_group)
        self.symbol = None  # каким символом представлен в матрице
        self.x_pos = None  # в матрице
        self.y_pos = None

    def create(self, x_pos, y_pos):
        if correct_coords(x_pos, y_pos, len(village[0]), len(village)):
            if not village[y_pos][x_pos]:
                if self.can_build():
                    village[y_pos][x_pos] = self.symbol
                    self.x_pos, self.y_pos = x_pos, y_pos
                    return True

    def can_build(self):  # проверяет, имеются ли ресурсы для постройки
        return True


class Barrack(Building):  # казарма
    def __init__(self):
        super.__init__()
        self.symbol = 'X'
        self.create(randrange(0, len(village[0])), randrange(0, len(village[0])))  # не надо создавать вручную

    def make_a_warrior(self):  # делает из незанятого героя воина, может вызываться при клике на картинку
        if resources['money'] and resources['free_people']:
            resources['money'] -= 3
            resources['warriors'].append(resources['free_people'].pop(0))
        return "Недостаточно ресурсов"


class House(Building):  # жилой дом
    def __init__(self):
        super.__init__()
        self.symbol = '^'
        self.time = 10 ** 6
        self.money_can_collect = False

    def create(self, x_pos, y_pos):
        if super.create(x_pos, y_pos):
            resources['money'] -= 20
            for _ in range(5):  # строится мгновенно и заселяется 5 героями
                resources['free_people'].append(Hero())

    def can_build(self):
        return resources['money'] >= 20

    def money(self):  # когда проходит время time можно собрать деньги (вызывется при каждом повторении игрового цикла)
        if clock.get_time() % self.time == 0:
            self.money_can_collect = True

    def collect_money(self):  # сбор денег, вызывается нажатием и работает, если заданное время прошло
        if self.money_can_collect:
            resources['money'] += 5
            self.money_can_collect = False  # деньги собраны


class Farm(Building):  # ферма
    def __init__(self):
        super.__init__()
        self.symbol = '*'
        self.time = 10 ** 9
        self.money_can_collect = False

    def create(self, x_pos, y_pos):
        if super.create(x_pos, y_pos):
            resources['money'] -= 10
            resources['farmers'].append(resources['free_people'].pop(0))  # один герой требуется в фермеры

    def can_build(self):
        return resources['money'] >= 10 and resources['free_people']

    def get_food(self):  # так как тут работает герой, еда собирается независимо от игрока
        resources['food'] += 7

    def money(self):  # когда проходит время time можно собрать деньги (вызывется при каждом повторении игрового цикла)
        if clock.get_time() % self.time == 0:
            self.money_can_collect = True

    def collect_money(self):  # сбор денег, вызывается нажатием и работает, если заданное время прошло
        if self.money_can_collect:
            resources['money'] += 5
            self.money_can_collect = False


class Hero(pygame.sprite.Sprite):
    def __init__(self):
        self.alive = 100  # уменьшается при уроне, голоде, востанавливается при питании.

    def can_live(self):  # вызывется при каждом повторении игрового цикла
        if not self.alive:
            self.die()

    def die(self):  # смерть - удаление из всех ресурсов, плюс групп спрайтов
        del resources['free_people'][resources['free_people'].index(self)]


class Warrior(Hero):
    def __init__(self):
        super.__init__()

    def die(self):
        del resources['warriors'][resources['warriors'].index(self)]


class Farmer(Hero):
    def __init__(self):
        super.__init__()

    def die(self):
        del resources['farmers'][resources['farmers'].index(self)]
