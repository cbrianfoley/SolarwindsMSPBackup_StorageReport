#!/usr/bin/env python3.7

#print(json.dumps(storageNodes, indent=4, sort_keys=True))

import json
import requests
import ssl

class swjsonapi:
# region constructor
	"""Access to Solarwinds JSON API

	Attributes:
		partnerName (str): 

	"""

	def __init__(self, partnerName, username, password, **kwargs):
		"""Create swjsonapi object and get an authorization token (visa) for future requests

		Args:
			partnerName (str): Solarwinds MSP Backup partner name
			username (str): Solarwinds MSP Backup username
			password (str): Solarwinds MSP Backup password, not available in object
		
		Keyword Args:
			url (str): URL for API endpoint, defaults to https://cloudbackup.management/jsonapi
			verify (str): path to SSL verification certificate, passed to request
			proxy (dict): URLs for http/https proxies, passed to request
			headers (dict): Override request headers, {"content-type": "application/json"} must be present!
		
		Returns:
			swjsonapi object
		"""

		self.partnerName = partnerName
		self.username = username
		# Create visa attribute
		self.visa = None
		self.requestOptions = {}
		
		if ("url" in kwargs):
			self.url = kwargs["url"]
		else:
			self.url = "https://cloudbackup.management/jsonapi"
		
		if ("proxies" in kwargs): self.requestOptions["proxies"] = kwargs["proxies"]
		if ("verify" in kwargs): self.requestOptions["verify"] = kwargs["verify"]
		
		if ("headers" in kwargs):
			self.requestOptions["headers"] = kwargs["headers"]
		else:
			self.requestOptions["headers"] = {"content-type": "application/json"}

		# Try to call Login to verify partnerName, username, and password
		try:
			partnerInfo = self._jsonCall("Login", {"partner":partnerName, "username":username, "password":password})
			self.partnerId = partnerInfo["result"]["PartnerId"]
		except:
			print("Unable to login - verify partner name/username/password or check proxy/ssl options")
# endregion

# region private methods
	def _jsonCall(self, method, params):
		"""Make a call to the json RPC API

		While this can be called directly, it is preferred to use the dedicated methods

		This method keeps track of and updates the authentication token (visa) transparently

		Args:
			method (str): API method to call
			params (dict): Parameters passed to method

		Returns:
			obj: Responce from API
		"""
		# Form the request, we are going to use the method name as the ID
		apiRequest = {
			"jsonrpc":"2.0",
			"method":method,
			"params":params,
			"id":method
		}

		# Visa should be present on all calls except the Login call
		if self.visa is not None:
			apiRequest["visa"] = self.visa

		apiResponse = requests.post(
			self.url,
			data=json.dumps(apiRequest),
			**self.requestOptions
		).json()

		# Store the visa from the result for the next call, any visa from the last 15 minutes will work
		self.visa = apiResponse["visa"]

		return apiResponse["result"]
# endregion

# region public class methods
	def getAccountInfoById(self, accountId):
		"""Get account information based on account ID

		Args:
			accountId (int): Account Id, can be retrived from enumerateAccounts
		"""
#		try:
		accountInfoById = self._jsonCall("GetAccountInfoById", {"accountId": accountId})
#		except:
#			print("Unable to get account information for account ID " + str(accountId))
		
		return accountInfoById

	def enumerateAccounts(self, partnerId):
		"""Enumerate accounts based on partner ID

		Args:
			partnerId (int): Partner Id, can be retrived from enumeratePartners
		"""
		try:
			accounts = self._jsonCall("EnumerateAccounts", {"partnerId": partnerId})
		except:
			print("Unable to enumerate accounts for partner ID " + str(partnerId))
		
		return accounts

	def enumerateAccountStatistics(self, query):
		"""Query account statistics

		Args:
			query (dict): Dictionary of parameters to query
				- PartnerId (int): Partner ID to query for
				- Filter (string):
				- ExcludedPartners (list): List of ints of partner IDs to exclude
				- SelectionMode (String): 

			   
               "Name" : "SelectionMode",
               "Type" : "AccountStatisticsSelectionMode::Enum"
               "Name" : "Labels",
               "Type" : "LabelCollection"
               "Name" : "StartRecordNumber",
               "Type" : "std::size_t"
               "Name" : "RecordsCount",
               "Type" : "std::size_t"
               "Name" : "OrderBy",
               "Type" : "std::string"
               "Name" : "Columns",
               "Type" : "ColumnVector"
               "Name" : "Totals",
               "Type" : "TotalVector"
		"""
#		try:
		enumAccountStats = self._jsonCall("EnumerateAccountStatistics", {"query":query})
#		except:
#			print("Unable to enumerate account statistics")
		
		return enumAccountStats

	def enumeratePartners(self, parentPartnerId, fetchRecursive, fields):
		"""Enumerate partners (customers) based on a given parent partner ID.

		Initial partner ID can be retrived from Login

		Args:
			partentPartnerId (int): Partner ID to enumerate sub-partners for
			fetchRecursive (str,bool): Whether to look for sub-partners of sub-partners
			fields (list): List of field data to return in the request
				- 0: Name
				- 1: Level
				- 3: ChildServiceTypes
				- 4: ServiceType
				- 5: State
				- 8: LocationId
				- 9: Flags
				- 10: Company Info
				- 18: EnternalCode, MailFrom
				- 20: CreationTime
		"""
		try:
			enumPartners = self._jsonCall("EnumeratePartners", {"parentPartnerId":parentPartnerId, "fields":fields, "fetchRecursively":fetchRecursive})
		except:
			print("Unable to enumerate partners for partner ID " + str(parentPartnerId))
		
		return enumPartners

	def enumerateStorageNodes(self, storageId):
		"""Enumerate storage nodes based on storage ID

		These are the actual servers/nodes, as opposed to storage pools

		Args:
			storageId (int): Storage pool Id, can be retrived from enumerateStorages
		"""
		try:
			storageNodes = self._jsonCall("EnumerateStorageNodes", {"storageId": storageId})
		except:
			print("Unable to enumerate storage nodes for storage ID " + str(storageId))
		
		return storageNodes

	def enumerateStorages(self, partnerId):
		"""Enumerate storage pools based on partner ID

		These are the pools, as opposed to storage servers/nodes

		Args:
			partnerId (int): Partner Id, can be retrived from enumeratePartners
		"""
		try:
			storages = self._jsonCall("EnumerateStorages", {"partnerId": partnerId})
		except:
			print("Unable to enumerate storage for partner ID " + str(partnerId))
		
		return storages

	def getAccountCustomColumnValues(self, accountId):
		"""Get account custom column values based on account ID

		This information is unfortunately not included in any other call

		Args:
			accountId (int): Account Id, can be retrived from enumerateAccounts
		"""
		try:
			accountCustomColumns = self._jsonCall("GetAccountCustomColumnValues", {"accountId": accountId})
		except:
			print("Unable to get custom column values for account ID " + str(accountId))
		
		return accountCustomColumns
	
	def getPartnerInfoById(self, partnerId):
		"""Get partner info based on partner ID

		Args:
			partnerId (int): Partner Id, can be retrived from enumeratePartners
		"""
		try:
			partnerInfo = self._jsonCall("GetPartnerInfoById", {"partnerId": partnerId})
		except:
			print("Unable to get partner info for partner ID " + str(partnerId))
		
		return partnerInfo
# endregion

# region public static methods
	def lookupOsType(type):
		os_types = {
			0:"Undefined",
			1:"Workstation",
			2:"Server"
		}
		if type in os_types:
			return os_types[type]
		else:
			raise ValueError("Invalid OS Type")

	def lookupStorageStatus(status):
		storage_statuses = {
			-2:"Offline",
			-1:"Failed",
			0:"Undefined",
			100:"Synchronized"
		}
		if status in storage_statuses:
			return storage_statuses[status]
		elif (status > 0) and (status < 100):
			return "Synchronizing " + str(status) + "%"
		else:
			raise ValueError("Invalid Storage Status")

	def lookupSeedingMode(mode):
		seeding_modes = {
			0:"Undefined",
			1:"Normal",
			2:"Seeding",
			3:"Preseeding",
			4:"Postseeding"
		}
		if mode in seeding_modes:
			return seeding_modes[mode]
		else:
			raise ValueError("Invalid Seeding Mode")

	def lookupLsvStatus(status):
		lsv_statuses = {
			-2:"Offline",
			-1:"Failed",
			0:"Undefined",
			100:"Synchronized"
		}
		if status in lsv_statuses:
			return lsv_statuses[status]
		elif (status > 0) and (status < 100):
			return "Synchronizing " + str(status) + "%"
		else:
			raise ValueError("Invalid LSV Status")

	def lookupBackupTypes(type):
		backup_types = {
			"D01":"Files and Folders",
			"D02":"System State",
			"D03":"MS SQL",
			"D04":"VSS Exchange",
			"D05":"Sharepoint Online",
			"D06":"Network Shares",
			"D07":"VSS System State",
			"D08":"VMware",
			"D09":"Total",
			"D10":"VSS MSSQL",
			"D11":"VSS Sharepoint",
			"D12":"Oracle",
			"D13":"Sims",
			"D14":"VSS Hyper-V",
			"D15":"MySQL",
			"D16":"Virtual Disaster Recovery",
			"D17":"Bare Metal Recovery",
			"D18":"Linux System State",
			"D19":"Exchange Online",
			"D20":"OneDrive Online"
		}
		if type in backup_types:
			return backup_types[type]
		else:
			raise ValueError("Invalid Backup Type")

	def lookupBackupStatus(status):
		backup_statuses = {
			0:"Undefined",
			1:"In Progress",
			2:"Failed",
			3:"Aborted",
			5:"Completed",
			6:"Interrupted",
			7:"Not Started",
			8:"Completed With Errors",
			9:"In Progress With Errors",
			10:"Over Quota",
			11:"No Selection",
			12:"Restarted"
		}
		if status in backup_statuses:
			return backup_statuses[status]
		else:
			raise ValueError("Invalid Backup Status")
# endregion