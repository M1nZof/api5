import requests
import os

from terminaltables import AsciiTable
from dotenv import load_dotenv


def vacancy_request_hh(vacancy, url):
    page = 0
    pages_number = 100
    vacancies = []
    
    while page < pages_number:
        payload = {
            'page': page,
            'text': vacancy
        }
        page_response = requests.get(url, params=payload)
        page_response.raise_for_status()

        page_payload = page_response.json()
        vacancies.append(page_payload)
        pages_number = page_payload['per_page']
        page += 1
    return vacancies


def vacancy_request_sj(vacancy, url):
    page = 0
    pages_number = 100
    vacancies = []
    
    while page < pages_number:
        headers = {
            'X-Api-App-Id': sj_key,
            'page': str(page),
            'count': str(100)
        }
        payload = {
            'page': page,
            'keywords': vacancy
        }
        page_response = requests.get(url, params=payload, headers=headers)
        page_response.raise_for_status()

        page_payload = page_response.json()
        vacancies.append(page_payload)
        pages_number = page_payload['total']
        page += 1

    return vacancies


def predict_salary(salary_from, salary_to):
    if salary_from and salary_to:
        return int((salary_from + salary_to) / 2)
    elif salary_from:
        return int(salary_from * 1.2)
    elif salary_to:
        return int(salary_to * 0.8)


def predict_rub_salary_hh(vacancy_response):
    salaries = []
    for vacancy in vacancy_response:
        vacancy_salary = vacancy.get('salary')
        if vacancy_salary and vacancy_salary.get('currency') == 'RUR':
            salaries.append(predict_salary(vacancy_salary.get('from'), vacancy_salary.get('to')))
    return salaries
   
   
def predict_rub_salary_sj(vacancy_response):
    salaries = []
    for vacancy in vacancy_response:
        if (vacancy.get('payment_from') or vacancy.get('payment_to')) and vacancy.get('currency') == 'rub':
            salaries.append(predict_salary(vacancy.get('payment_from'), vacancy.get('payment_to')))
    return salaries

   
def get_statistics_hh():
    for language in languages:
        language_request = vacancy_request_hh(language, 'https://api.hh.ru/vacancies')
        page_salaries_lenght = 0
        page_salaries_sum = 0
        for request_page in language_request:
            page_salaries = predict_rub_salary_hh(request_page['items'])
            page_salaries_sum += sum(page_salaries)
            page_salaries_lenght += len(page_salaries)
        vacancies_found = language_request[0]['found']
        
        vacancies_salaries_hh_and_sj['HeadHunter Moscow'][language] = {
            'vacancies_found': vacancies_found,
            'vacancies_processed': page_salaries_lenght,
            'average_salary': int(page_salaries_sum / page_salaries_lenght)
            }
    return vacancies_salaries_hh_and_sj


def get_statistics_sj():
    for language in languages:
        language_request = vacancy_request_sj(language, 'https://api.superjob.ru/2.0/vacancies/')
        page_salaries_lenght = 0
        page_salaries_sum = 0
        for request_page in language_request:
            page_salaries = predict_rub_salary_sj(request_page['objects'])
            page_salaries_sum += sum(page_salaries)
            page_salaries_lenght += len(page_salaries)
        vacancies_found = language_request[0]['total']
        
        vacancies_salaries_hh_and_sj['SuperJob Moscow'][language] = {
            'vacancies_found': vacancies_found,
            'vacancies_processed': page_salaries_lenght,
            'average_salary': int(page_salaries_sum / page_salaries_lenght)
            }
    return vacancies_salaries_hh_and_sj


if __name__ == '__main__':
    load_dotenv()
    sj_key = os.environ['SJ_KEY']

    languages = ['Python', 'JS', 'Java', 'Ruby', 'PHP', 'C', 'CSS', 'GO']
    quantity_of_vacancies = {}
    vacancies_salaries_hh_and_sj = {
        'HeadHunter Moscow': {},
        'SuperJob Moscow': {}
    }

    for job_area in [get_statistics_hh(), get_statistics_sj()]:
        for key, languages in job_area.items():
            table_data = [
                ['Язык программирования', 'Вакансий найдено', 'Вакансий обработано', 'Средняя зарплата'],
            ]
            for language, values in languages.items():
                language_data = [language, values['vacancies_found'],
                                 values['vacancies_processed'], values['average_salary']]
                table_data.append(language_data)
            table = AsciiTable(table_data=table_data, title=key)
            print(table.table)
            del table, table_data
