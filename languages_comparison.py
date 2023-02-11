import requests
import os

from terminaltables import AsciiTable
from dotenv import load_dotenv


def get_vacansies_hh(language, url):
    page = 0
    pages_number = 100
    vacancies = []
    
    while page < pages_number:
        payload = {
            'page': page,
            'text': language
        }
        page_response = requests.get(url, params=payload)
        page_response.raise_for_status()

        page_payload = page_response.json()
        vacancies.append(page_payload)
        pages_number = page_payload['per_page']
        page += 1
    return vacancies


def get_vacansies_sj(language, url, sj_key):
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
            'keywords': language
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


def predict_rub_salary_hh(vacancies):
    salaries = []
    for vacancy in vacancies:
        vacancy_salary = vacancy.get('salary')
        if vacancy_salary and vacancy_salary.get('currency') == 'RUR':
            predicted_salary = predict_salary(vacancy_salary.get('from'), vacancy_salary.get('to'))
            if predicted_salary:
                salaries.append(predict_salary(vacancy_salary.get('from'), vacancy_salary.get('to')))
    return salaries
   
   
def predict_rub_salary_sj(vacancies):
    salaries = []
    for vacancy in vacancies:
        if (vacancy.get('payment_from') or vacancy.get('payment_to')) and vacancy.get('currency') == 'rub':
            salaries.append(predict_salary(vacancy.get('payment_from'), vacancy.get('payment_to')))
    return salaries

   
def get_statistics_hh(languages, job_area_statistic):
    for language in languages:
        vacancies = get_vacansies_hh(language, 'https://api.hh.ru/vacancies')
        page_salaries_lenght = 0
        page_salaries_sum = 0
        for request_page in vacancies:
            page_salaries = predict_rub_salary_hh(request_page['items'])
            page_salaries_sum += sum(page_salaries)
            page_salaries_lenght += len(page_salaries)
        vacancies_found = vacancies[0]['found']
        try:
            average_salary = page_salaries_sum / page_salaries_lenght
        except ZeroDivisionError:
            continue
        job_area_statistic[language] = {
            'vacancies_found': vacancies_found,
            'vacancies_processed': page_salaries_lenght,
            'average_salary': int(average_salary)
            }


def get_statistics_sj(languages, job_area_statistic, sj_key):
    for language in languages:
        vacancies = get_vacansies_sj(language, 'https://api.superjob.ru/2.0/vacancies/', sj_key)
        page_salaries_lenght = 0
        page_salaries_sum = 0
        for request_page in vacancies:
            page_salaries = predict_rub_salary_sj(request_page['objects'])
            page_salaries_sum += sum(page_salaries)
            page_salaries_lenght += len(page_salaries)
        vacancies_found = vacancies[0]['total']
        try:
            average_salary = page_salaries_sum / page_salaries_lenght
        except ZeroDivisionError:
            continue

        job_area_statistic[language] = {
            'vacancies_found': vacancies_found,
            'vacancies_processed': page_salaries_lenght,
            'average_salary': int(average_salary)
            }


def print_tables(job_statistics):
    for job_area, language in job_statistics.items():
        table_data = [
                ['Язык программирования', 'Вакансий найдено', 'Вакансий обработано', 'Средняя зарплата'],
            ]    
        for language_name, language_results in language.items():
            language_packed_results = [language_name, language_results['vacancies_found'],
                                      language_results['vacancies_processed'], language_results['average_salary']]
            table_data.append(language_packed_results)
        table = AsciiTable(table_data=table_data, title=job_area)
        print(table.table)

if __name__ == '__main__':
    load_dotenv()
    sj_key = os.environ['SJ_KEY']

    languages = ['Python', 'JS', 'Java', 'Ruby', 'PHP', 'C', 'CSS', 'GO']
    job_statistics = {
        'HeadHunter Moscow': {},
        'SuperJob Moscow': {}
    }
    
    job_statistics['HeadHunter Moscow'] = {}
    job_statistics['SuperJob Moscow'] = {}
    
    get_statistics_hh(languages, job_statistics['HeadHunter Moscow']) 
    get_statistics_sj(languages, job_statistics['SuperJob Moscow'], sj_key)
    
    print_tables(job_statistics)
