import time
import pandas as pd
import numpy as np
from selenium import webdriver
from collections import OrderedDict
from bs4 import BeautifulSoup
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from tqdm import tqdm
import csv

def click_driver_element(game,driver):
    "Используем библиотеку selenium для поиска и клика"
    url = "https://www.esrb.org/search/"
    driver.get(url)
    enter = driver.find_element("css selector", "#content > div > div > form > div.field > input")
    enter.clear()
    enter.send_keys(game)
    driver.find_element("css selector", '#content > div > div > form > div.submit > button').click()
    WebDriverWait(driver, 15).until(ec.presence_of_element_located((By.CLASS_NAME, "paginate")))
    return driver.page_source, driver.current_url

def search_woking_link(game,driver):
    "Ищет ссылку с карточками информацией"
    html, url = click_driver_element(game,driver)
    soup = BeautifulSoup(html,"html.parser")
    h4 = soup.find_all("h4")
    "Убираем последнее слова, пока не появятся карточки с информацией или запрос не будет составлять меньше 2 слов"
    while soup.find_all("h4") and len(game.split(' ')) > 2:
        game= " ".join(game.split(' ')[:-1])
        html, url = click_driver_element(game, driver)
        soup = BeautifulSoup(html,"html.parser")
    if soup.find_all("h4"):
        return None, url
    else:
        return soup, url

def search_gamename_rating(soup):
    "Ищем названия игры и рейтинг игры"
    dict = {}
    class_games = soup.find_all(class_="game")
    for class_game in class_games:
        dict[class_game.find("h2").text.lower()] = class_game.find(class_="content").find("img")['alt']
    return dict


def main_search(edit_name_games,game,games_ratings,game_names,driver):
    "Данный метод реализует главную функцию - поиск значений рейтинга ESRB"
    exit = []
    start_time = time.time()
    index = edit_name_games.index(game) # если в edit_name_games искомая игра на 5 месте, то и в game_names она будет на 5 месте
    print(game)
    print(index)
    soup, url = search_woking_link(game,driver)
    if soup != None:
        try:
            max_page = int(soup.find_all(lambda tag: tag.name == 'a' and
                                                     tag.get('class') == ['page-numbers'])[-1].text.replace(",",""))
            if max_page > 100:
                games_ratings[game_names[index]] = None
                print("--- %s seconds ---" % (time.time() - start_time), '\n')
                return games_ratings
        except:
            max_page = 1
        temp_dictone_game = {} # создаем временный словарь для хранения всех названия игр по нашему запросу
        for i in range(max_page):
            dict_onerequest = search_gamename_rating(soup)
            temp_dictone_game.update(dict_onerequest)
            "Уменьшаем время выполнения запроса: ищем полное соответствие с названим игры и названием найденных карточками игр"
            for n in range(len(dict_onerequest)):
                list_onerequest = list(dict_onerequest.keys())
                if game.lower() == list_onerequest[n]:
                    games_ratings[game_names[index]] = dict_onerequest[list_onerequest[n]]
                    print(temp_dictone_game)
                    print("--- %s seconds ---" % (time.time() - start_time), '\n')
                    return games_ratings
                    exit = game
                    break
            if exit != []:
                break
            if max_page == 1:
                break
            if i == max_page-1:
                break
            url = url.replace(f'pg={i + 1}', f'pg={i + 2}')
            driver.get(url)
            WebDriverWait(driver, 25).until(ec.presence_of_element_located((By.CLASS_NAME, "game")))
            soup = BeautifulSoup(driver.page_source,"html.parser")
        if exit != []:
            return games_ratings
        change_game = game
        "Удаляем по 1 слову с конца пока не будет совпадения - для запросов больше 1 слова"
        "Повышает точность. правильность и скорость полученных данных"
        while len(change_game.split(' ')) >= 2:
            for i in range(len(temp_dictone_game)):
                list_onerequest = list(temp_dictone_game.keys())
                if change_game.lower() == list_onerequest[i]:
                    games_ratings[game_names[index]] = temp_dictone_game[list_onerequest[i]]
                    print("--- %s seconds ---" % (time.time() - start_time), '\n')
                    return games_ratings
                    exit = game
                    break
            if exit == []:
                change_game = " ".join(change_game.split(' ')[:-1])
            else:
                break
        "Проверяем запросы с запросов по одному слову"
        if len(change_game.split(' ')) < 2:
            list_onerequest = list(temp_dictone_game.keys())
            for i in range(len(temp_dictone_game)):
                if change_game.lower() == list_onerequest[i]:
                    games_ratings[game_names[index]] = temp_dictone_game[list_onerequest[i]]
                    print("--- %s seconds ---" % (time.time() - start_time), '\n')
                    return games_ratings
                    exit = game
                    break
            if exit == []:
                if len(list_onerequest) != []:
                    try:
                        games_ratings[game_names[index]] = temp_dictone_game[list_onerequest[0]]
                        print("--- %s seconds ---" % (time.time() - start_time), '\n')
                        return games_ratings
                    except:
                        games_ratings[game_names[index]] = None
                        print("--- %s seconds ---" % (time.time() - start_time), '\n')
                        return games_ratings
                else:
                    games_ratings[game_names[index]] = None
                    print("--- %s seconds ---" % (time.time() - start_time), '\n')
                    return games_ratings
    else:
        games_ratings[game_names[index]] = None
        print("--- %s seconds ---" % (time.time() - start_time), '\n')
        return games_ratings

def save_file(df):
    "Сохраняем каждое значение в csv фаил"
    df_game = pd.DataFrame(list(df.items()), columns=['Name', 'Rating'])
    df_game.to_csv('Game_ratings.csv', index=False)


def main():
    "Задаем настройки webdriver, считываем данные с csv файл, обрабатываем данные, получаем рейтинг ESRB"

    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    driver = webdriver.Chrome(options=options)

    "В файле csv хранятся, только названия игр"
    with open('Processed_Data_Example.csv', newline='') as File:
        reader = csv.reader(File)
        game_names = [] # сохраняем оригинальные названия
        for row in reader:
            game_names.extend(row)

    "Обрабатываем названия игр"
    edit_name_games = [] # сохраняет измененные названия игр
    for game_name in game_names:
        edit_name_games.append((str(game_name).split('/')[0]).strip()) #обрабатываем названия

    games_ratings = {} # сохраем словарь куда будем записывать данные: игра - рейтинг
    "Перебираем названия игр"
    for game in tqdm(edit_name_games):
        save_file(main_search(edit_name_games, game, games_ratings,game_names,driver)) # метод возвращает заполненый словарь (+1 игра)
    "Вывод результаты в консоли"
    for key, value in games_ratings.items():
        print(key, ' - ', value)
    print('\n')

if __name__ == "__main__":
    main()
