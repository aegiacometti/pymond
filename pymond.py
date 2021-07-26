#!/usr/bin/python3
"""
Small script to monitor a service, store the result and HTTP serve the files.
"""
import json
import subprocess
import sys
import os
from time import sleep
from datetime import datetime
from threading import Thread
import http.server
from requests.auth import HTTPBasicAuth
import socketserver
import requests
import config

data_path = "/".join([os.path.dirname(os.path.realpath(sys.argv[0])), config.data_dir])


def clean_old_samples(service_file):
    file_list = [x for x in os.listdir(data_path) if x.endswith('.json')]
    for service in service_file:
        service_files = [x for x in file_list if x.startswith(service)]
        num_service_samples = len(service_files)
        if num_service_samples > config.samples_to_keep:
            service_files.sort()
            for file in service_files[:-config.samples_to_keep]:
                os.remove("/".join([data_path, file]))


def web_server(dp):
    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=dp, **kwargs)
    with socketserver.TCPServer(("", config.http_port), Handler) as httpd:
        httpd.serve_forever()


def post_to_elk(log_message):
    headers = {'Content-Type': 'application/json'}
    auth = HTTPBasicAuth(config.elk_user, config.elk_password)
    requests.post(config.elk_url, auth=auth, headers=headers,
                  json=json.loads(log_message),
                  timeout=config.pause_between_checks)


def check_services():
    for service in config.services:
        try:
            stdout = subprocess.check_output(['service', service, 'status']).decode(sys.stdout.encoding)

        except subprocess.CalledProcessError:
            status = 'error'

        else:
            if stdout.find('Active: active (running)'):
                status = 'up'

            else:
                status = 'down'

        now = datetime.now()
        date = now.strftime("%Y-%m-%d-%H-%M-%S")
        log_message = '{"service":"' + service + '", "date":"' + date + '", "status": "' + status + '"}'
        with open(f'{data_path}/{service}-{date}-{status}.json', 'w') as file:
            file.write(log_message)

        if config.elk_enabled:
            post_to_elk(log_message)


def start():
    # Init
    if not os.path.exists(data_path):
        os.mkdir(data_path)

    if config.web_server_enabled:
        web = Thread(target=web_server, args=(data_path,))
        web.start()

    # Start
    while True:
        check_services()
        clean_old_samples(config.services)
        sleep(config.pause_between_checks)


if __name__ == "__main__":
    start()
