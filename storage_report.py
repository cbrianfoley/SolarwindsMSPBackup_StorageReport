#!/usr/bin/env python3.7

import csv
import json
import logging
import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.utils import formatdate
from email import encoders
from datetime import datetime, timedelta
from sw_msp_backup_json_api import swjsonapi

# Get the time for reporting script run time
startTime = datetime.now()

config = {
    "partner_name":"insertpartnernamehere",
    "username":"insertusernamehere",
    "password":"insertpasswordhere",
    "csv_file_name":"storage_report.csv",
    "log_file_name":"storage_report.txt",
    "log_file_level":"INFO",
    "log_console_level":"DEBUG",
    "mail_server":"insertmailserverhere",
    "mail_port":"insertportnumberhere",
    "mail_user":"insertmailuserhere",
    "mail_destination":"insertmaildestinationhere",
    "customer_filter":None,
    "account_filter":None,
    "debug_mode":False
}

# Setup base logging
logger = logging.getLogger("backup.report.threaded")
# Base logger must be set to DEBUG to get anything more verbose than WARNING, even if individual handlers use more verbose levels
# So we will set the base logger to the most verbose level
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s : %(levelname)s :\t %(message)s')

# Setup console logging
ch = logging.StreamHandler()
ch.setLevel(config["log_console_level"])
ch.setFormatter(formatter)
logger.addHandler(ch)

# Setup file logging if config is set
if config["log_file_name"] is not None:
    fh = logging.FileHandler(config["log_file_name"])
    fh.setLevel(config["log_file_level"])
    fh.setFormatter(formatter)
    logger.addHandler(fh)

logger.info("Script start time: " + startTime.strftime("%H:%M:%S"))

# Result Dict
customerData = {}

logger.debug("Getting Solarwinds json auth data...")
mspbackupapi = swjsonapi(config["partner_name"], config["username"], config["password"])
logger.debug("Solarwinds auth OK - Partner ID is " + str(mspbackupapi.partnerId))

logger.debug("Building list of customers...")
# build list of customers using our swjsonapi
customers = mspbackupapi.enumeratePartners(mspbackupapi.partnerId,"true",[0,10])["result"]

# get all storage nodes
storagenodes = mspbackupapi.enumerateStorages(mspbackupapi.partnerId)

# setup list for eventual write to csv
storagereportlist = []

for customer in customers:
    logger.debug("Customer: " + customer["Name"])

    # See if we need to filter by customer
    if config["customer_filter"] is not None:
        if customer["Id"] != config["customer_filter"]:
            logger.debug("Customer rejected by filter")
            continue

    # Create sub-dict for customer
    customerData[customer["Id"]] = {}
    # Easier access
    cd = customerData[customer["Id"]]

    cd["CustomerId"] = customer["Id"]
    cd["Name"] = customer["Name"]

    accountsQueryParams = {
        "PartnerId":cd["CustomerId"],
        "StartRecordNumber":0,
        "RecordsCount":100,
        "Columns":[
            "I1",       # Device Name
        ]
    }

    logger.debug(" Retrieving Accounts...")
    accounts = mspbackupapi.enumerateAccountStatistics(accountsQueryParams)["result"]

    if accounts is None:
        logger.warn("No accounts found in customer " + customer["Name"])
        continue
    
    logger.debug(" Accounts found")
    
    for account in accounts:

        # Data columns are dicts within a dict with keys of the column number. This can be variable sized, so there
        # isn't a reliable way of going through the dict to find what we need, so this takes and merges all of
        # the sub dicts to one dict we can work with
        columns = {}
        for iColumn in account["Settings"]:
            for colName, colVal in iColumn.items():
                columns[colName] = colVal

        logger.debug("  Account: " + columns["I1"])

        # See if we need to filter by account
        if config["account_filter"] is not None:
            if account["AccountId"] != config["account_filter"]:
                logger.debug("Account rejected by filter")
                continue
                
        #get node info
        accountNodeInfo = mspbackupapi.getAccountInfoById(account["AccountId"])
        #get ID of storage node
        accountStorageNodeId = accountNodeInfo['result']['StorageId']
        #lookup name of storage node
        for storageid in storagenodes['result']:
            if storageid['Id'] == accountStorageNodeId:
                accountStorageName = storageid['Name']
        logger.debug("   StorageNode: " + accountStorageName)
        
        # put info in list to be written as a line item
        storagereportlist.append([customer["Name"],columns["I1"],accountStorageName])

# make our csv file
with open(config["csv_file_name"], 'w', newline='') as file:
    wr = csv.writer(file, quoting=csv.QUOTE_ALL)
    for lineitem in storagereportlist:
        wr.writerow(lineitem)

# email it

# make the email
msg = MIMEMultipart()
msg['Subject'] = "MSP Backup Storage Report " + config["partner_name"]
msg['From'] = config["mail_user"]
msg['To'] = config["mail_destination"]
msg['Date'] = formatdate(localtime = True)
body='''
<!DOCTYPE html>
<html>
<body>

<p><font face="Tahoma" size=2> See attached.</p></font> 

</body>
</html>
'''
msg.attach(MIMEText(body, 'html'))
# attach the attachment
part=MIMEBase('text','csv')
part.set_payload(open(config['csv_file_name'],'rb').read())
encoders.encode_base64(part)
part.add_header('Content-Disposition', 'attachment; filename="{0}"'.format(os.path.basename(config['csv_file_name'])))
msg.attach(part)
# send the mail (a few more lines could add SSL/TLS support)
mail=smtplib.SMTP(config['mail_server'],config['mail_port'])
mail.ehlo()
mail.sendmail(config['mail_user'],config['mail_destination'],msg.as_string())
    
logger.debug("Email Sent")
    
logger.info("Script start time: " + startTime.strftime("%H:%M:%S"))
logger.info("Script end time: " + datetime.now().strftime("%H:%M:%S"))

exit()