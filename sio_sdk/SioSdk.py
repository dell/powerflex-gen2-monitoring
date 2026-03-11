# Copyright 2026 Dell, Inc.
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

"""
Usage: 'import SioSdk'

Allows easy authentication & requests to the PowerFlex Gateway REST API
"""
import datetime
import sys
import json
import requests
import time

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

def err(*args):
    """
        Print arguments in Standard Error output with "[datetime]" prefix
    """
    prt = ' '.join(map(str, args))
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    sys.stderr.write("["+now+"] "+prt+"\n")

class SioRestException(Exception):
    pass

class SioRestClient(object):
    """
        PowerFlex REST API request helper class
    """
    def __init__(self, host, user, passw, verifySSL=False):
        self.__hostname = host
        self.__username = user
        self.__password = passw
        self.__ssl = verifySSL
        self.__access_token = None
        self.__refresh_token = None
        self.__token_expiry = None
        self.__refresh_token_expiry = None

    def __login(self):
        """
            Authenticate using the new REST login endpoint
            Returns access token and refresh token
        """
        try:
            login_url = 'https://{0}/rest/auth/login'.format(self.__hostname)
            payload = {
                'username': self.__username,
                'password': self.__password
            }
            
            req = requests.post(
                login_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                proxies={'http': None, 'https': None},
                verify=self.__ssl)
            
            if req.status_code != 200:
                raise SioRestException(req.content.decode('utf-8'))
            
            response_data = req.json()
            self.__access_token = response_data.get('access_token')
            self.__refresh_token = response_data.get('refresh_token')
            
            # Set token expiry times (access tokens are valid for 5 minutes per PowerFlex documentation)
            self.__token_expiry = time.time() + (5 * 60)  # 5 minutes
            # Refresh tokens expire in 30 minutes
            self.__refresh_token_expiry = time.time() + (30 * 60)  # 30 minutes
            
        except requests.exceptions.RequestException as error:
            err(error)
            sys.exit(2)
    
    def __refresh_access_token(self):
        """
            Use refresh token to get new access token without re-authenticating
        """
        try:
            refresh_url = 'https://{0}/rest/auth/update-token'.format(self.__hostname)
            payload = {
                'refresh_token': self.__refresh_token
            }
            
            req = requests.post(
                refresh_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                proxies={'http': None, 'https': None},
                verify=self.__ssl)

            if req.status_code != 200:
                # Refresh token expired or invalid, need to login again
                err("Refresh token invalid or expired; re-authenticating")
                self.__login()
                return

            response_data = req.json()
            self.__access_token = response_data.get('access_token')
            # Update refresh token if server returns a new one
            new_refresh = response_data.get('refresh_token')
            if new_refresh:
                self.__refresh_token = new_refresh
                self.__refresh_token_expiry = time.time() + (30 * 60)  # reset window
            self.__token_expiry = time.time() + (5 * 60)  # 5 minutes
            err("Refreshed access token using refresh token")

        except requests.exceptions.RequestException as error:
            err(error)
            sys.exit(2)
    
    def __ensure_valid_token(self):
        """
            Ensure we have a valid access token, refresh if needed
        """
        if self.__access_token is None:
            self.__login()
        elif time.time() >= self.__token_expiry:
            if self.__refresh_token and time.time() < self.__refresh_token_expiry:
                self.__refresh_access_token()
            else:
                self.__login()

    def get_json(self, urlpath):
        """
            Create a GET Request to the PowerFlex API with .../urlpath URI
            Return a JSON parsed object.
        """
        self.__ensure_valid_token()
        try:
            req = requests.get(
                'https://{0}/{1}'.format(self.__hostname, urlpath.lstrip('/')),
                headers={'Authorization': 'Bearer {0}'.format(self.__access_token)},
                proxies={'http': None, 'https': None},
                verify=self.__ssl)
            if req.status_code != 200:
                raise SioRestException(req.content.decode('utf-8'))
            return json.loads(req.content.decode('utf-8'))
        except requests.exceptions.RequestException as error:
            err(error)
            sys.exit(2)
        return None

    def post_json(self, urlpath, data):
        """
            Create a POST Request to the PowerFlex API with .../urlpath URI
            Include the "data" JSON parsed object in body.
            Return a JSON parsed object.
        """
        self.__ensure_valid_token()
        try:
            req = requests.post(
                'https://{0}/{1}'.format(self.__hostname, urlpath.lstrip('/')),
                headers={
                    'Authorization': 'Bearer {0}'.format(self.__access_token),
                    'Content-type': 'application/json'
                },
                data=json.dumps(data),
                proxies={'http': None, 'https': None},
                verify=self.__ssl)
            if req.status_code != 200:
                raise SioRestException(req.content.decode('utf-8'))
            return json.loads(req.content.decode('utf-8'))
        except requests.exceptions.RequestException as error:
            err(error)
            sys.exit(2)
        return None
