import copy
import datetime
import json
import sys
import os
import dateutil
from pandas import ExcelWriter
import config
import requests
import pandas


def authenticate(platform, username, password):
    ### Authentication
    ### returns token in body - 'acess_token': '[token]'
    url = platform + '/v1/auth/'
    payload = str({"username": username, "password": password}).replace("'", '"')
    headers = {'Content-Type': 'application/json'}

    response = requests.request('POST', url, headers=headers, data=payload)
    print(response)

    if response.status_code == 200:
        token = json.loads(response.text)['access_token']
        return token
    else:
        # This means something went wrong.
        raise Exception('GET ' + url + ' {}'.format(response.status_code))


def get_children_list(platform, token):
    ### Get children list
    children_list = []

    print('\nGetting children list...')

    for page in range(1, 1000):
        print(str(page) + ' ', end='', flush=True)

        url = platform + '/v1/children/?page=' + str(page)
        payload = {}
        headers = {
            'Authorization': 'Bearer ' + token,
            'Content-Type': 'application/json'
        }

        response = requests.request('GET', url, headers=headers, data=payload)

        if response.status_code == 200:
            res = json.loads(response.text)
            if res:
                children_list.extend(res)
            else:
                break
        else:
            # This means something went wrong.
            raise Exception('GET ' + url + ' {}'.format(response.status_code))
    print()

    return children_list


def get_children_missions(platform, token, children_list):
    children_missions = []
    print('\nGetting children missions...')
    for i, child in enumerate(children_list, 1):
        print(str(i) + ' ', end='', flush=True)

        url = platform + '/v1/observations/get-all-missions/' + child['id']
        payload = {}
        headers = {
            'Authorization': 'Bearer ' + token,
            'Content-Type': 'application/json'
        }
        response = requests.request('GET', url, headers=headers, data=payload)
        if response.status_code == 200:
            res = json.loads(response.text)['data']
            for mission in res:
                start_date = dateutil.parser.parse(mission['startDate'])
                completed_date = dateutil.parser.parse(mission['completedDate'])
                created_at = dateutil.parser.parse(mission['createdAt'])
                updated_at = dateutil.parser.parse(mission['updatedAt'])

                updict = {'child_username': child['username'],
                          'child_id': child['id'],
                          'id': mission['id'],
                          'type': mission['type'],
                          'questionnaire': mission['questionnaire'],
                          'goal': mission['goal'],
                          'question': mission['question'],
                          'mission_id': mission['mission']['id'],
                          'mission_label': mission['mission']['label'],
                          'mission_severity': mission['mission']['severity'],
                          'mission_missionTitle': mission['mission']['missionTitle'],
                          'mission_childMessage': mission['mission']['childMessage'],
                          'progress': mission['progress'],
                          'recommendations_id': mission['recommendations']['id'],
                          'recommendations_child': mission['recommendations']['childRecommendation'],
                          'recommendations_parent': mission['recommendations']['parentRecommendation'],
                          'activeStatus': mission['activeStatus'],
                          'validationStatus': mission['validationStatus'],
                          'creatorId': mission['creatorId'],
                          'startDate': start_date.strftime('%d/%m/%Y'),
                          'completedDate': completed_date.strftime('%d/%m/%Y'),
                          'weekNumber': mission['weekNumber'],
                          'year': mission['year'],
                          'createdAt': created_at.strftime('%d/%m/%Y'),
                          'updatedAt': updated_at.strftime('%d/%m/%Y')}
                children_missions.append(updict)
        else:
            # This means something went wrong.
            raise Exception('GET ' + url + ' {}'.format(response.status_code))

    return children_missions


def get_dss(platform, token, children_list):
    # get dss list
    children_dss = []

    print('\nGetting children DSS list...')
    for i, child in enumerate(children_list, 1):
        print(str(i) + ' ', end='', flush=True)

        url = platform + '/v1/observations/get-all-child-questionnaires/' + child['id']
        payload = {}
        headers = {
            'Authorization': 'Bearer ' + token,
            'Content-Type': 'application/json'
        }
        response = requests.request('GET', url, headers=headers, data=payload)
        if response.status_code == 200:
            res = json.loads(response.text)['data']
            for dss in res:
                updict = {'child_username': child['username'],
                          'child_id': child['id'],
                          'week': dss['week'],
                          'year': dss['year']}
                for question in dss['questions']:
                    updict_copy = copy.deepcopy(updict)
                    updict2 = {'questionnaireId': question['questionnaireId'],
                               'question_text': question['question']['text']}
                    updict_copy.update(updict2)
                    if not question['answers']:
                        children_dss.append(updict_copy)
                    else:
                        for answer in question['answers']:
                            updict_copy2 = copy.deepcopy(updict_copy)
                            d = dateutil.parser.parse(answer['answeredAt'])
                            updict3 = {'answers': answer['answer'],
                                       'answeredAt': d.strftime('%d/%m/%Y'),
                                       'absweredBy': answer['absweredBy']}
                            updict_copy2.update(updict3)
                            children_dss.append(updict_copy2)
        else:
            # This means something went wrong.
            raise Exception('GET ' + url + ' {}'.format(response.status_code))

    return children_dss


def save_files(path, list_to_save, json_filename, csv_filename, xlsx_filename):
    date = datetime.datetime.now().strftime('%d-%m-%Y')

    # Save JSON file
    with open(path + '/' + json_filename + date + ".json", 'w') as outfile:
        json.dump(list_to_save, outfile, indent=4, ensure_ascii=False)

    outfile.close()
    # Convert JSON to CSV
    with open(path + '/' + json_filename + date + ".json", encoding='utf-8-sig') as outfile:
        df = pandas.read_json(outfile)

    df.to_csv(path + '/' + csv_filename + date + ".csv", encoding='utf-8', index=False)

    # json_to_csv(path+'/'+config.JSON_FILE_NAME_DSS, path+'/'+config.CSV_FILE_NAME_DSS)

    # Convert CSV to Excel (.xlsx)
    with ExcelWriter(path + '/' + xlsx_filename + date + ".xlsx", date_format='DD-MM-YYYY',
                     datetime_format='DD-MM-YYYY HH:MM:SS') as ew:
        pandas.read_csv(path + '/' + csv_filename + date + ".csv").to_excel(ew, sheet_name=csv_filename)
    # csv_to_excel(path+'/'+config.CSV_FILE_NAME_DSS, path+'/'+config.XLSX_FILE_NAME_DSS)
    outfile.close()


# ----------------- MAIN -----------------
def main():
    print("OCARIoT Plaform Export")

    # Create a path for EU files to be saved to
    path = datetime.datetime.now().strftime('%d-%m-%Y') + '/EU'
    os.makedirs(path, exist_ok=True)

    # Get authentication token for EU platform
    username = config.username_eu
    password = config.password_eu
    token = authenticate(config.PLATFORM_URL_EU, username, password)

    # Get children list from the EU Platform
    children_list = get_children_list(config.PLATFORM_URL_EU, token)
    # Get required data associated with EU childrens
    dss_list = get_dss(config.PLATFORM_URL_EU, token, children_list)

    print('\nSaving EU DSS files ...')
    save_files(path, dss_list, config.JSON_FILE_NAME_DSS, config.CSV_FILE_NAME_DSS, config.XLSX_FILE_NAME_DSS)
    print('JSON, CSV and Excel files saved')

    missions = get_children_missions(config.PLATFORM_URL_EU, token, children_list)

    print('\nSaving EU Mission files ...')
    save_files(path, missions, config.JSON_FILE_NAME_Missions, config.CSV_FILE_NAME_Missions,
               config.XLSX_FILE_NAME_Missions)
    print('JSON, CSV and Excel files saved')

    # Create a path for BR files to be saved to
    path = datetime.datetime.now().strftime('%d-%m-%Y') + '/BR'
    os.makedirs(path, exist_ok=True)

    # Get authentication token for BR platform
    username = config.username_br
    password = config.password_br
    token = authenticate(config.PLATFORM_URL_BR, username, password)

    # Get children list from the BR Platform
    children_list = get_children_list(config.PLATFORM_URL_BR, token)

    # Get required data associated with BR children
    dss_list = get_dss(config.PLATFORM_URL_BR, token, children_list)

    print('\nSaving BR DSS files ...')
    save_files(path, dss_list, config.JSON_FILE_NAME_DSS, config.CSV_FILE_NAME_DSS, config.XLSX_FILE_NAME_DSS)
    print('JSON, CSV and Excel files saved')

    missions = get_children_missions(config.PLATFORM_URL_BR, token, children_list)

    print('\nSaving BR Mission files ...')
    save_files(path, missions, config.JSON_FILE_NAME_Missions, config.CSV_FILE_NAME_Missions,
               config.XLSX_FILE_NAME_Missions)
    print('JSON, CSV and Excel files saved')


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nReceived Keyboard Interrupt! Exiting...')
        sys.exit(0)
    except Exception:
        print('\nAn error occurred! Exiting...\n')
        import traceback

        traceback.print_exc()
        sys.exit(1)
