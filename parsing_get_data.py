# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
import requests
import pandas as pd
from datetime import date


# get html code from url
def get_html(url: str): 
  headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
  rq = requests.get(url, headers=headers)
  print('Gettin HTML-code from ', url)
  return rq.text


# проверяет, есть ли на странице ссылки на вакансии
def is_empty(html):
    soup = BeautifulSoup(html, 'lxml')
    links = soup.find_all('a', class_='bloko-link HH-LinkModifier')
    if links == []:
        return True
    else:
        return False

# get vacancies lins from search current page
def get_offers_links(html):
  soup = BeautifulSoup(html, 'lxml')

  link_parsed = []
  links = soup.find_all('a', class_='bloko-link HH-LinkModifier')
  for link in links:
      link_parsed.append(link.get('href').split('?')[0])
      
  return link_parsed


# get all vacancies links on search request
def get_all_links(query, area):
  url_base = 'https://hh.ru/search/vacancy'
  url_text = '?text=' + '+'.join(query)
  url_area = '&area=' + str(area)
  url_page = '&page='

  page_is_not_empty = True

  all_links = []
  page = 0

  while page_is_not_empty:
    url = url_base + url_text + url_area + url_page + str(page)
    # time.sleep(.5)
    html = get_html(url)

    # # temp code
    # if page == 1: break

    if not is_empty(html):
      all_links += get_offers_links(html)
      page += 1
    else:
      page_is_not_empty = False          

  return all_links


# parsing from vacancies links
def parsing(links):
  column_names = ['ID', 'Title', 'Wage', 'Key Skills']
  data = pd.DataFrame(columns = column_names)
  for link in links:
    html = get_html(link)
    soup = BeautifulSoup(html, 'lxml')


    try:
      # get ID
      ID = link.split('/')[-1]

      # get vacancy title
      vac_title = soup.find('h1').get_text()

      # get company name
      comp_name = soup.find('div', {'class': 'vacancy-company-name-wrapper'}).get_text()

      # get address
      tag_adddress = soup.find('p', {'data-qa': 'vacancy-view-location'})
      job_address = list(tag_adddress.stripped_strings)
      # get metro stations 
      metro = [x.text for x in tag_adddress.find_all('span', {'class': 'metro-station'})]
      # remove commas
      while ',' in job_address: job_address.remove(',')
      for x in job_address:
        if x not in metro:
          city = x
          break

      # get wage
      wage = soup.find('span', {'class': 'bloko-header-2 bloko-header-2_lite'}).get_text().replace(u'\xa0', '')

      # get experience
      exper = soup.find('span', {'data-qa' : 'vacancy-experience'}).get_text()

      # get employment and timetable
      employment_tags = soup.find('p', {'data-qa': 'vacancy-view-employment-mode'})
      employment_text = list(employment_tags.stripped_strings)
      # remove commas
      while ',' in employment_text: employment_text.remove(',')
      timetable = employment_tags.find('span').get_text()
      for x in employment_text:
        if x not in timetable:
          employment = x
          break

      # get skills
      skills = []
      skills_tag = soup.find_all('span', {'data-qa': 'bloko-tag__text'})  
      for skill_tag in skills_tag:
        # skills += skill_tag.text + ', '  
        skills.append(skill_tag.text)
         
      data_temp = pd.DataFrame({'ID':ID, 
                                'Title': vac_title, 
                                'Wage': wage,
                                'Employment': employment,
                                'Timetable': timetable,
                                'Key Skills': [skills], 
                                'Experience': exper,
                                'Company_name': comp_name,
                                'City': city,
                                'link': link})
      data = data.append(data_temp, ignore_index=True)
    except:
      print('exception in ', link)
  return data

if __name__ == "__main__":
  query = ['analyst', 'python']
  links = get_all_links(query, 1)
  data = parsing(links)
  data.to_csv('vacancy_data_' + '_'.join(query) + '_' + date.today().strftime('%d%m%Y') + '.csv')
  print('Checked', len(links), 'job vacancies.')