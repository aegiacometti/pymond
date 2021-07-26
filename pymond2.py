#!/usr/bin/python3
"""
Small script to monitor a systemd service and ICMP connectivity.
Then based on config.py it can:
 - store the result
 - HTTP serve the files
 - Trigger an action like a webhook
"""

import subprocess
import sys
import os
import re
from time import sleep
from datetime import datetime
from threading import Thread
from concurrent.futures import ThreadPoolExecutor
import http.server
import socketserver
import requests
from requests.auth import HTTPBasicAuth
import json
import config2 as config

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
        print("serving at port", config.http_port)
        httpd.serve_forever()


def post_to_elk(log_message):
    headers = {'Content-Type': 'application/json'}
    auth = HTTPBasicAuth(config.elk_user, config.elk_password)
    requests.post(config.elk_url, auth=auth, headers=headers, json=json.loads(log_message))


def post_to_slack(log_message):
    headers = {'Content-Type': 'application/json'}
    message = {"text": log_message}
    requests.post(config.slack_webhook, headers=headers, json=message)


def check_services(service, prev_status):
    try:
        stdout = subprocess.check_output(['service', service, 'status']).decode(sys.stdout.encoding)

    except subprocess.CalledProcessError:
        status = 'error'

    else:
        if stdout.find('Active: active (running)'):
            status = 'up'

        else:
            status = 'down'

    logging(service, status, prev_status)


def logging(svc, sts, prev_status):
    now = datetime.now()
    date = now.strftime("%Y-%m-%d-%H-%M-%S")
    log_message = '{"service":"' + svc + '", "date":"' + date + '", "status": "' + sts + '"}'
    with open(f'{data_path}/{svc}-{date}-{sts}.json', 'w') as file:
        file.write(log_message)

    if config.elk_enabled:
        post_to_elk(log_message)

    if config.slack_enabled and prev_status[svc] != sts:
        post_to_slack(f'Service {svc} - {sts}')
        prev_status[svc] = sts


def check_ip_address(ip_address, prev_status):
    try:
        stdout = subprocess.check_output(['ping',
                                          f'-c {config.count}',
                                          f'-W {config.timeout}',
                                          ip_address]).decode(sys.stdout.encoding)

    except subprocess.CalledProcessError:
        status = 'down'

    else:
        match = re.search(r'(.*) packets transmitted, (.*) received', stdout)
        if match.group(1) == match.group(2):
            status = 'up'
        else:
            status = 'loss'

    logging(ip_address, status, prev_status)


def start():
    # Init
    if not os.path.exists(data_path):
        os.mkdir(data_path)

    if config.web_server_enabled:
        web = Thread(target=web_server, args=(data_path,))
        web.start()

    service_previous_status = {}
    for service in config.services:
        service_previous_status[service] = 'up'

    ip_previous_status = {}
    for ip_address in config.ip_addresses:
        ip_previous_status[ip_address] = 'up'

    # Start
    while True:
        with ThreadPoolExecutor() as executor:

            for service in config.services:
                executor.submit(check_services, service, service_previous_status)

            for ip_address in config.ip_addresses:
                executor.submit(check_ip_address, ip_address, ip_previous_status)

        clean_old_samples(config.services)
        clean_old_samples(config.ip_addresses)
        sleep(config.pause_between_checks)


if __name__ == "__main__":
    start()
