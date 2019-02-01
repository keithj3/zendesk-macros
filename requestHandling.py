'''
Handles common User Services requests
to the Zendesk API.
'''

import time
import requests

from creds import ZD_KEY, ZD_EMAIL, agent_email


def zendesk_auth(use_admin=False):
    '''
    Establishes session
    '''
    if not use_admin:
        email = agent_email
    else:
        email = ZD_EMAIL
    uname = '{}/token'.format(email)
    headers = {'Content-Type': 'application/json'}
    auth = (uname, ZD_KEY)
    session = requests.Session()
    session.auth = auth
    session.headers = headers
    return session

class ZendeskSession():
    '''
    Connection to ZD API.
    '''

    def __init__(self, session=None, **kwargs):

        if 'url' in kwargs:
            self.url = kwargs.pop('url')

        if 'payload' in kwargs:
            self.payload = kwargs.pop('payload')

        if 'method' in kwargs:
            self.method = kwargs.pop('method')

        if 'verbose' in kwargs:
            self.verbose = kwargs.pop('verbose')
        else:
            self.verbose = False

        if session is None:
            self.session = zendesk_auth()
        else:
            self.session = session


    def get_response(self):
        '''
        Use to handle common ZD error responses.
        Pass verbose=True to print statements
        '''
        if not hasattr(self, 'url'):
            raise Exception('Must pass a url as kwarg.')

        if not hasattr(self, 'method'):
            raise Exception('Must pass an http method.')

        if not hasattr(self, 'payload'):

            commands = {
                'get': self.session.get(self.url),
                'post': self.session.post(self.url),
                'put': self.session.put(self.url),
                'delete': self.session.delete(self.url)
                }
        else:

            commands = {
                'post': self.session.post(self.url, data=self.payload),
                'put': self.session.put(self.url, data=self.payload)
                }

        total_attempts, retry_429, retry_409, retry_500 = 0, 0, 0, 0


        while total_attempts < 7:

            response = commands[self.method]
            if self.verbose:
                print('{} returned {}'.format(self.url, response.status_code))

            if response.status_code in [200, 201, 204]:
                return response

            #422, 400
            if response.status_code in [400, 422]:
                if self.verbose:
                    print(response.status_code, str(response.content[:1000]), response.__dict__)
                return None

            # 429
            while response.status_code == 429 and retry_429 < 3:
                if 'Retry-After' in response.headers:
                    retry_seconds = response.headers['Retry-After'] + 1
                    if self.verbose:
                        print('Pausing for rate limit ({} of 3) {} secs.'.format(retry_429, \
                                                                                 retry_seconds))
                    time.sleep(retry_seconds)
                else:
                    if self.verbose:
                        print('429 response but no "retry-after" so waiting 20 seconds.')
                        time.sleep(20)

                retry_429 += 1
                total_attempts += 1

            #409
            while response.status_code == 409 and retry_409 < 3:
                if self.verbose:
                    print('Response code 409. Merge conflict? Retrying {} of 3.'.format(retry_409))
                time.sleep(3)
                retry_409 += 1
                total_attempts += 1

            #500s
            while (500 < response.status_code < 599) and (retry_500 < 2):
                if 'Retry-After' in response.headers:
                    retry_seconds = response.headers['Retry-After'] + 1
                    if self.verbose:
                        print('Pausing for 500 error ({} of 2) {} secs.'.format(retry_500, \
                                                                                retry_seconds))
                    time.sleep(retry_seconds)
                    retry_500 += 1
                    total_attempts += 1

                else:
                    if self.verbose:
                        print('500 response but no "retry-after" so waiting 20 seconds.')
                    time.sleep(20)
                retry_500 += 1
                total_attempts += 1

            total_attempts += 1
 
        return None
