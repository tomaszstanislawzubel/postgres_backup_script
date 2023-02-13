# postgres backup scripts

**Script for the automation of postgres dump backups with:**

* weekly/monthly schedule for generating dumps
* validation and removal of files older than 3 weeks(for weekly script) and 3 months(for monthly script) from production server
* file compression to .zip archive and password protection
* mail notifications of generating and sending database dumps to external server
* sending dumps to external server via scp protocol

<br>

## Script details / crontab config
---
Both scripts will be configured over `.../workspace` on root account's crontab as following:

`5 4 * * 6 /usr/bin/python3 /path/postgres_backup_script/postgres_backup_script_weekly.py
10 4 20 * * /usr/bin/python3 /path/postgres_backup_script/postgres_backup_script_monthly.py`

with difference being to execute scripts weekly and monthly. By default scripts will generate backups to the root directory of application, this will be: `.../workspace`, in form of password-protected .zip archive. Password for archives will be the same as password for ssh connection to production server. For the moments backups will go to remote directory: `.../workspace` at (`.../workspace`). This SMB share is mounted under `.../workspace` server as mount under `.../workspace/path`, which make it easier to manage/check stats as part of local file system mount to remote storage. Dumps can be downloaded from share by configuring it to be accessed as network share under operating system or with the usage of apps for file system remote sessions supporting SCP protocol, like WinSCP.

Mail messaging with notifications can require additional checks over the google account, because of access over the application password - user of the mailbox will need to open the mail/account management to approve attempt of access to gmail account from running script on server.

Last three backups will be stored over the production server location, on the SMB share scripts is configured to remove files with creation date older than one year. With compressed .zip archive and 200GB of available space at the moment`*` dumps with the size about 330MB should not take much space and they should not exhaust the available space on the share. In the future script can be extended with other way of checking/clearing space, depending on scale of increase speed of dump size.

`*` - `specific user case`

<br>

## Requirements
---

`pip3 install pyminizip
smtplib
paramiko` on system's configured python3(not venv, as scripts runs outside `.../workspace`)

`sudo apt-get install cifs-utils` to give possibility to mount SMB share under OS for backup storage

Script will also require to configure mailing service under `/etc/ssmtp/ssmtp.conf` to send out messages with backup reports/storage stats of backup share.