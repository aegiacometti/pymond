"""
Configure your sample retention period according to the following formula

   x minutes = pause between checks in seconds * samples to keep / 60

   1 week = 300 * x / 60
   x = 1 week * 60 /300 => 2016 samples to keep

 1 hour = 60 minutes
 24 hs = 1 day = 1.440 minutes
 1 week = 10.080 minutes
 1 month = 43.200 minutes aprox
 3 months = 129.600 minutes aprox
"""

pause_between_checks = 60
samples_to_keep = 300

# specify you data directory for storing the check results
data_dir = './data/'

# List your systemd services to check
services = ['sshd', 'containerd']

# List your IP to test ping
ip_addresses = ['8.8.8.8']

# Post to external tool
elk_enabled = False
elk_url = 'https://api.example.com/api/dir/v1/monitor/uptime/example'
elk_user = '123'
elk_password = '456'

# Slack Webhook
slack_enabled = True
slack_webhook = 'https://hooks.slack.com/services/xxx/yyy/zzz'

web_server_enabled = True
http_port = 8000
