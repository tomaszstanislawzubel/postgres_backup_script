#!/usr/bin/python3
import os
import re
import shutil
import datetime
import pyminizip
import smtplib
from email.message import EmailMessage
import time
import apt

share_ip_addr = '1.2.3.4'
zip_password = 'test'

#one year in seconds
three_months_in_seconds = 7890000

def smb_share_validation():
    #checking if cifs-utils are installed to mount smb share
    cache = apt.Cache()
    if cache`'cifs-utils'`.is_installed:
        pass
    else:
        os.system('apt install -y cifs-utils')
    #checking if smb share is configured or not
    with open('/etc/fstab') as f:
        if '//{}/smbshare /media/backup cifs credentials=/path/to/.smbcredentials,iocharset=utf8 0 0'.format(share_ip_addr) in f.read():
            pass
        else:
            with open('/etc/fstab', 'a') as f:
                f.write('//{}/smbshare /media/backup cifs credentials=/path/to/.smbcredentials,iocharset=utf8 0 0'.format(share_ip_addr))
    if os.path.exists('path/to/.smbcredentials') == True:
        os.system('mount -a')
    else:
        with open('path/to/.smbcredentials', mode = "w") as f:
            f.write('username=smbuser' + "\n" + 'password=smbpassword')
            os.system('mount -a')

#actual backup task: listing of old zip files, cleaning if needed(3 weeks/3months plus, depends on which script is running),
#generating fresh dump, zipping it, sending to remote smb share, cleaning of dumps older than one year
def backup_task(occurence, occurence_short, occurence_seconds):
    zip_files = list()
    os.chdir("/path/postgres_backup_script/postgres_{}".format(occurence))

    for file in os.listdir("."):
        if file.endswith(".zip"):
            zip_files.append(file)

    for file in zip_files:
        if (datetime.datetime.now()-datetime.datetime.fromtimestamp(os.stat(file).st_ctime)).total_seconds() <= occurence_seconds:
            pass
        else:
            if os.path.exists(file):
                os.remove(file)
            else:
                print("File does not exists.")

    os.system("sudo -u postgres pg_dump -U postgres -d database > dump_{}.sql".format(datetime.date.today()))
    for file in os.listdir("."):
        if file.endswith(".sql"):
            compression_level = 9
            pyminizip.compress(file, ".", str(file).strip('.sql')+"{}.zip".format(occurence_short), zip_password, compression_level)
            shutil.copyfile("/path/postgres_backup_script/postgres_{}/".format(occurence)+str(file).strip('.sql')+"{}.zip".format(occurence_short), '/media/backup/'+str(file).strip('.sql')+"{}.zip".format(occurence_short))
            os.remove(file)

    os.chdir('/media/backup/')

    for file in os.listdir("."):
        if file.endswith(".zip"):
            if (datetime.datetime.now()-datetime.datetime.fromtimestamp(os.stat(file).st_ctime)).total_seconds() <= three_months_in_seconds:
                pass
            else:
                if os.path.exists(file):
                    os.remove(file)
                else:
                    print("File does not exists.")

#generating of prod and remote smb listings, preparing and sending mail message with report
def send_postgres_backup_reports(occurence, sql_dump_name):
    directory_listing = os.popen('ls -lsha').read() + "\n"
    time.sleep(3) #awaiting to add all zip files to directory_listing variable, mail messasing can hang out on this step

    cbs_total, cbs_used, cbs_free = shutil.disk_usage('/media/backup')

    EMAIL_ADDRESS = os.environ`'EMAIL_ADDRESS'`
    EMAIL_PASSWORD = os.environ`'EMAIL_PASSWORD'`

    message_body = "Hello, \n" \
        "This is to notify you that following app database dump from postgresql server \n" \
        + sql_dump_name + " " +\
        "has been generated, packed and sent to external backup server. \n" \
        "Current content and stats of SMB share: \n" \
        "total: %s GiB" % (cbs_total // (2**30)) + "\n" \
        "used: %s GiB" % (cbs_used // (2**30)) + "\n" \
        "free: %s GiB" % (cbs_free // (2**30)) + "\n" \
        "%s" % os.popen('ls -lsha').read() + "\n" \
        "Current content on production server /path/postgres_backup_script/postgres_monthly directory:  \n"
    time.sleep(3) #awaiting to add all zip files to directory_listing variable, mail messasing can hang out on this step
    msg_to_be_sent = message_body + directory_listing

    #file app.env have configuration of notification adresses, we can pull out mails and script
    #should be aware about any changes of notification mails in future
    f=open("/path/app.env", "r")
    adresses_string=""
    for i in f.readlines():
        line = re.findall(r'NOTIFICATION_ADDRESSES', i)
        if line:
            adresses_string=i

    adresses = list(adresses_string.split(" "))
    #striping variable name from variable`0` to have only email addresses in the list
    adresses`0`=adresses`0`.replace("NOTIFICATION_ADDRESSES='", "")

    msg = EmailMessage()
    msg`'Subject'` = '`app` Postgres app database dump created ({} script)'.format(occurence)
    msg`'From'` = EMAIL_ADDRESS
    #replacing earlier hardcoded addresses with output of app.env file read from above
    recipients = adresses
    msg`'To'` = ", ".join(recipients)
    msg.set_content(msg_to_be_sent)

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)
