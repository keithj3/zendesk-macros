'''
Put a personal macro id in the creds file and it will pull the macro
and copy it to a universal macro
'''

import json

import creds
import requestHandling as rh

#Put Agent Email and Macro ID in creds file!


def get_personal_macro():
    ''' returns all personal agent macros'''
    macros = []
    next_page = creds.ZD_BASE_URL + 'macros.json?access=personal'
    while next_page is not None:
        data = rh.ZendeskSession(url=next_page, method='get').get_response().json()
        for _macro in data['macros']:
            macros.append(_macro)
        next_page = data['next_page']
        print(next_page)

    for macro in macros:
        if macro['id'] == creds.macro_id:
            return macro

    raise Exception('The agent macro is not in the agent\'s personal macros.')

def save_macro(macro):
    '''put macro in temp json file'''
    with open('macro.json', 'w') as file:
        json.dump(macro, file)

def change_creds():
    '''log in as admin instead of user'''
    return rh.zendesk_auth(use_admin=True)

def get_new_macro_payload():
    '''take the json file and make a payload for creating a new macro'''
    with open('macro.json', 'r') as file:
        old_macro = json.load(file)
        title = old_macro['title']
        actions = old_macro['actions']
        return json.dumps({'macro': {'title': title, 'actions': actions}})

def create_new_macro(session, payload):
    '''use new session to write the new macro'''
    url = creds.ZD_BASE_URL + 'macros.json'
    return rh.ZendeskSession(session=session, url=url, method='post',
                             payload=payload, verbose=True).get_response().json()

if __name__ == '__main__':

    personal_macro = get_personal_macro()
    save_macro(personal_macro)
    session = change_creds()
    payload = get_new_macro_payload()
    new_macro = create_new_macro(session, payload)
    print('New macro created. Response: {}'.format(new_macro))









