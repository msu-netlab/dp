import base64
import dns.message
import requests
import json

ripe_response_json_string = requests.get('https://atlas.ripe.net/api/v1/measurement/1669107/result/').text
ripe_response_json = json.loads(ripe_response_json_string)
loop_one = 0
domain_name = 'fbcdn-profile-a.akamaihd.net'
url = 'http://www.cs.montana.edu/~utkarsh.goel/scripts/dns/ripe_insert.php'
while loop_one < len(ripe_response_json):
	loop_two = 0;
	while loop_two < len(ripe_response_json[loop_one]['resultset']):
		dnsmsg = dns.message.from_wire(base64.b64decode(ripe_response_json[loop_one]['resultset'][loop_two]['result']['abuf']))
		answer = dnsmsg.answer
		noOfAnswerObjects = len(answer)
		noOfIp = len(answer[noOfAnswerObjects - 1])
		loop = 0 
		while loop < noOfIp:
			data = { 'app_server_ip': str(answer[noOfAnswerObjects - 1][loop]), 'domain_name': domain_name, 'type': 'ripe_dns' }
			print str(answer[noOfAnswerObjects - 1][loop])
			try:
				requests.post(url, data=data).text
				print "Recorded."
			except:
				print "error"
			loop = loop + 1
		loop_two = loop_two + 1
	loop_one = loop_one + 1