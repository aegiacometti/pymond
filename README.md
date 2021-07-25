Simple Python3 script to monitor systemd services.

You don't need to install any library.

It can:
 - log status to different files per service including the date and status 
 - http serve the directory for remote view
 - post a JSON doc to ElasticStack. Note it could be a post to Influxdb/Grafana

### Setup

1. Configure your parameters in `config.py`
2. Set your userID and installation directory in the file `pymond.service`
3. The copy that file to `/usr/lib/systemd/system`
4. Finally, start the service
`sudo systemctl start pymond`
5. Optionally you may want to enable auto-start at boot run this command
`sudo systemctl pymond.service enable`

#### One step further

Version 2 can also check ICMP connectivity and send Slack Alerts.

Refer to pymond2.py and config2.py files and update pymond.service.
