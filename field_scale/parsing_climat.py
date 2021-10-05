
from selenium import webdriver

import time

def get_weather(first, last):
    driver = webdriver.Chrome()


    driver.get(url="https://rp5.ru/%D0%90%D1%80%D1%85%D0%B8%D0%B2_%D0%BF%D0%BE%D0%B3%D0%BE%D0%B4%D1%8B_%D0%B2_%D0%91%D1%83%D0%B4%D0%B5%D0%BD%D0%BD%D0%BE%D0%B2%D1%81%D0%BA%D0%B5")


    driver.find_element_by_id("tabSynopDLoad").click()

    driver.find_element_by_xpath(".//*[contains(text(), 'CSV (текстовый)')]").click()
    time.sleep(3)


    first_date = driver.find_element_by_id("calender_dload")
    first_date.clear()
    first_date.send_keys(first_date)


    last_date = driver.find_element_by_id('calender_dload2')
    last_date.clear()
    last_date.send_keys(last_date)

    time.sleep(3)


    driver.find_element_by_xpath(".//*[contains(text(), 'Выбрать в файл GZ')]").click()

    time.sleep(5)


    link =  driver.find_element_by_link_text("Скачать").get_property('href')

  
    return(link)

