import csv

data = [{
    'money_of_farm': 7,
    'money_of_house': 5,
    'money_of_barrak': 100,
    'time_of_barrak': 10 ** 4,
    'time_of_house': 10 ** 3,
    'time_of_farm': 10 ** 3 * 5,
    'time_of_food': 10 * 10,
    'food_of_farm': 10,
    'battle_time': 10
}]

with open('data/settings.csv', 'w', newline='') as f:
    writer = csv.DictWriter(
        f, fieldnames=list(data[0].keys()),
        delimiter=';', quoting=csv.QUOTE_NONNUMERIC)
    writer.writeheader()
    for d in data:
        writer.writerow(d)
