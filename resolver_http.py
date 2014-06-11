import dns.resolver
import requests
import time
import uuid

def processDomain(dns_server_ip, domain_name):
	request_id = uuid.uuid4()
	url = "http://www.cs.montana.edu/~utkarsh.goel/scripts/dns/insert.php"
	my_resolver = dns.resolver.Resolver()
	my_resolver.nameservers = [dns_server_ip]
	answer = my_resolver.query(domain_name)
	noOfAnswerObjects = len(answer.response.answer)
	noOfIp = len(answer.response.answer[noOfAnswerObjects - 1])
	loop = 0 
	while loop < noOfIp:
		is_alive = 0;
		app_Server_ip = str(answer.response.answer[noOfAnswerObjects - 1][loop])
		try:
			http_head_resp = requests.request('HEAD', "http://" + app_Server_ip, timeout=1)
			is_alive = 1
		except:
			is_alive = 0
			print "error"
		data = { 'dns_ip': dns_server_ip, 'app_server_ip': app_Server_ip, 'domain_name': domain_name, 'is_alive': is_alive, 'type': 'http_head', 'req_id': request_id }
		try:
			requests.post(url, data=data).text
		except:
			print "error"
		loop = loop + 1

def createLookup(dns_array, domain_array):
	dns_array_loop = 0
	while dns_array_loop < len(dns_array):
		domain_array_loop = 0
		while domain_array_loop < len(domain_array):
			processDomain(dns_array[dns_array_loop], domain_array[domain_array_loop])
			domain_array_loop = domain_array_loop + 1
		dns_array_loop = dns_array_loop + 1

def getDnsDomainList():
	try:
		dns_domain_list = requests.post('http://www.cs.montana.edu/~utkarsh.goel/scripts/dns/dns_domain_list.php').text
		dns_array = (dns_domain_list.split(':')[0]).split(',')
		domain_array = (dns_domain_list.split(':')[1]).split(',')
		createLookup(dns_array, domain_array)
	except:
		print "error in obtaining dns_domain list"

while 1:
	getDnsDomainList()
	time.sleep(600)