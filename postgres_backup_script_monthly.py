#!/usr/bin/python3
import postgres_backup_configuration
import datetime

#name of dump to be generated
sql_dump_name = "dump_{}.sql".format(datetime.date.today())
#definition of occurence of the script to be executed
occurence = "monthly"
occurence_short = "m"
#three months measured in seconds: 7776000
#three weeks measured in seconds: 1814400
occurence_seconds = 7776000

postgres_backup_configuration.smb_share_validation()
postgres_backup_configuration.backup_task(occurence, occurence_short, occurence_seconds)
postgres_backup_configuration.send_postgres_backup_reports(occurence, sql_dump_name)