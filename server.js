var dgram = require("dgram");
var http =  require("http");
var dnsIpList = ["8.8.8.8", "208.67.222.222", "209.244.0.3"];
var server = dgram.createSocket("udp4");
server.bind(53);
var domainToIpArray = {};
var IpPerformanceArray = {};

server.on("error", function (err) {
	console.log("server error:\n" + err.stack);
	server.close();
});

server.on("message", function (msg, rinfo) {
	var clientReq = msg.toString('hex', 0, msg.length);
	if(clientReq.substr(clientReq.length - 8, 4) == "0001") {
		var count = 1, avg = 0, min=Number.MAX_VALUE, minIp = "", countAvg = 0;
		var domainNameInHex = clientReq.substr(24, clientReq.length - 32);
		var clientIp = rinfo.address;
		var clientPort = rinfo.port;
		var isDnsResponseSentToClient = false;
		var dnsResponseToSendTransactionId = clientReq.substr(0, 4);
		var ipArray = [];
		
		if (typeof domainToIpArray[domainNameInHex] === "undefined") {
			var message = new Buffer(msg);
			var client = dgram.createSocket("udp4");
			
			client.on('error', function(err) {
				console.log("UDP Bind Error: " + err);
			});
			
			client.bind();
			
			dnsIpList.forEach(function(dnsIp) {
				client.send(message, 0, message.length, 53, dnsIp, function(err, bytes) {
					if (err) {
						console.log("Error in forwarding DNS request to " + dnsIp);
					}
					else if(bytes) {
						//console.log("DNS request forwarded to" + dnsIp);
					}
				});
			});
			
			setTimeout(function() { 
				client.close(); 
				ipArray = ipArray.filter (function (v, i, a) { return a.indexOf (v) == i });
				evaluateIpAddress(ipArray);
			}, 2000);
			
			
			
			client.on("message", function (msg, rinfo) {
				var freshDomainIp = parseIpFromDnsResponse(msg);		
				if(!isDnsResponseSentToClient && freshDomainIp != 0) {
					var freshDomainTtl = "00000004";
					var dnsPacketInHexWithoutTransactionId = "818000010001" + clientReq.substr(16) + "c00c00010001" + freshDomainTtl + "0004" +freshDomainIp;
					var dnsResponseToSend = dnsResponseToSendTransactionId + dnsPacketInHexWithoutTransactionId;
					sendDnsResponse(dnsResponseToSend, clientIp, clientPort);
					domainToIpArray[domainNameInHex] = {'ip': freshDomainIp, 'ttl': freshDomainTtl, 'dnsPacketInHexWithoutTransactionId' : dnsPacketInHexWithoutTransactionId};
				}
				else if (!isDnsResponseSentToClient && freshDomainIp == 0) {
					sendDnsResponse(msg.toString('hex', 0, msg.length), clientIp, clientPort);
				}
				if(freshDomainIp != 0) {
					processDnsResponse(msg);
				}
			});
		
		}
		else {
			var dnsResponseFromCache = dnsResponseToSendTransactionId + domainToIpArray[domainNameInHex]['dnsPacketInHexWithoutTransactionId'];
			sendDnsResponse(dnsResponseFromCache, clientIp, clientPort);
		}
		
		
		function parseIpFromDnsResponse(msg) {
			var resInString = msg.toString('hex', 0 , msg.length);
			var isAuthority = parseInt(resInString.substr(16, 4), 16);
			var newResponse = resInString + "";
			if (!isAuthority) {
				newResponse = "";
				var noOfAnswer = parseInt(resInString.substr(12, 4), 16);
				var posAfterQuery = resInString.indexOf("00010001", 24);
				newResponse = resInString.substr(0, posAfterQuery + 8);
				var resAfterQuery = resInString.substr(posAfterQuery + 8);
				var loop = 0;
				var initialStart = 0;
				var currentAnswerCount = noOfAnswer;
				while (loop < noOfAnswer) {
					var dataLength = parseInt(resAfterQuery.substr(20, 4), 16);
					var answerLength = 24 + (dataLength * 2);
					var answer = resAfterQuery.substr(initialStart, answerLength);
					if (dataLength != 4 && currentAnswerCount > 1) {
						resAfterQuery = resAfterQuery.replace(answer, "");
						currentAnswerCount = currentAnswerCount - 1;
					}
					else if(dataLength == 4) {
						return answer.substr(answer.length - 8);
					}
					loop++;
				}
			}
			else {
				return 0;
			}
			 
		}

		function sendDnsResponse(msg, ip, port) {
			var message = new Buffer(msg, 'hex');
			server.send(message, 0, message.length, port, ip, function(err, bytes) {
				if (err) {
					console.log("Error sending DNS response to client");
				}
				else if (bytes) {
					isDnsResponseSentToClient = true;
					console.log("response sent to client");
				}			
			});
		}
		
		function processDnsResponse(msg) {
			var resInString = msg.toString('hex', 0 , msg.length);
			var isAuthority = parseInt(resInString.substr(16, 4), 16);
			var newResponse = resInString + "";
			if (!isAuthority) {
				newResponse = "";
				var noOfAnswer = parseInt(resInString.substr(12, 4), 16);
				var posAfterQuery = resInString.indexOf("00010001", 24);
				newResponse = newResponse + resInString.substr(0, posAfterQuery + 8);
				var resAfterQuery = resInString.substr(posAfterQuery + 8);
				var loop = 0;
				var initialStart = 0;
				while (loop < noOfAnswer) {
					var dataLength = parseInt(resAfterQuery.substr(20,4), 16);
					var answerLength = 24 + (dataLength * 2);
					var answer = resAfterQuery.substr(initialStart, answerLength);
					if(dataLength == 4) {
						var ip = answer.substr(answer.length - 8);
						var ipTtl = answer.substr(12, 8);
						ipArray.push(parseInt(ip.substr(0, 2), 16) + "." + parseInt(ip.substr(2, 2), 16) + "." + parseInt(ip.substr(4, 2), 16) + "." + parseInt(ip.substr(6, 2), 16));
					}
					loop++;
					resAfterQuery = resAfterQuery.substr(answerLength);
				}
			}
		}

		function evaluateIpAddress(ipList){
			if(ipList.length > 0){
				var options = {method: 'HEAD', host: ipList[0], port: 80, path: '/'};
				var initialTimestamp = new Date().getTime();
				var req = http.request(options, function(res) {
					var timeToHead = (new Date().getTime() - initialTimestamp);
					avg += timeToHead;
					if(count === 3){
						count = 1;
						countAvg++;
						avg = avg/countAvg;
						if(avg < min){
							min = avg;
							minIp = ipList[0];
							var ipSegments = minIp.split('.');
							var newDomainToIpArrayString = "818000010001" + clientReq.substr(16) + "c00c00010001" + "00000004" + "0004";
							for (var loop = 0; loop < ipSegments.length; loop++) {
								var tempIpSegmentInHex = parseInt(ipSegments[loop]).toString(16);
								newDomainToIpArrayString = newDomainToIpArrayString + ("00" + tempIpSegmentInHex).substr(tempIpSegmentInHex.length);
							}
							domainToIpArray[domainNameInHex]['dnsPacketInHexWithoutTransactionId'] = newDomainToIpArrayString;
						}
						avg = 0;
						countAvg = 0;
						evaluateIpAddress(ipList.splice(1));
					}
					else {
						evaluateIpAddress(ipList);
						count++;
						countAvg ++;
					}
				});

				req.on('error', function(e) {
					console.log("Got error: " + e.stack);
					if(count === 3){
						count = 1;
						if(countAvg > 0){
							avg = avg/countAvg;
							if(avg < min){
								min = avg;
								minIp = ipList[0];
								var ipSegments = minIp.split('.');
								var newDomainToIpArrayString = "818000010001" + clientReq.substr(16) + "c00c00010001" + "00000004" + "0004";
								for (var loop = 0; loop < ipSegments.length; loop++) {
									var tempIpSegmentInHex = parseInt(ipSegments[loop]).toString(16);
									newDomainToIpArrayString = newDomainToIpArrayString + ("00" + tempIpSegmentInHex).substr(tempIpSegmentInHex.length);
								}
								domainToIpArray[domainNameInHex]['dnsPacketInHexWithoutTransactionId'] = newDomainToIpArrayString;
							}
						}
						avg = 0;
						countAvg = 0;
						evaluateIpAddress(ipList.splice(1));
					}
					else {
						evaluateIpAddress(ipList);
						count++;
					}
				});
				
				req.end();
		   }
		   
		}
		
	}
});


/*

var ifIpProcessed = 0;
				if (typeof IpPerformanceArray[domainNameInHex] === "undefined") {
					IpPerformanceArray[domainNameInHex] = domainNameInHex;
					IpPerformanceArray[domainNameInHex]['ip'] = ip;
					IpPerformanceArray[domainNameInHex]['timeToHead'] = timeToHead;
					IpPerformanceArray[domainNameInHex]['count'] = 1;
					ifIpProcessed = 1;
				}
				else if (IpPerformanceArray[domainNameInHex]['ip'] == ip && (IpPerformanceArray[domainNameInHex]['timeToHead'] > ((IpPerformanceArray[domainNameInHex]['timeToHead'] * IpPerformanceArray[domainNameInHex]['count']) + timeToHead)/(IpPerformanceArray[domainNameInHex]['count'] + 1))) {
					IpPerformanceArray[domainNameInHex]['timeToHead'] = ((IpPerformanceArray[domainNameInHex]['timeToHead'] * IpPerformanceArray[domainNameInHex]['count']) + timeToHead)/(IpPerformanceArray[domainNameInHex]['count'] + 1);
					IpPerformanceArray[domainNameInHex]['count'] = IpPerformanceArray[domainNameInHex]['count'] + 1;
					ifIpProcessed = 1;
				}
				else if (IpPerformanceArray[domainNameInHex]['ip'] != ip && IpPerformanceArray[domainNameInHex]['timeToHead'] > timeToHead) {
					IpPerformanceArray[domainNameInHex]['ip'] = ip;
					IpPerformanceArray[domainNameInHex]['timeToHead'] = timeToHead;
					IpPerformanceArray[domainNameInHex]['count'] = 1;
					ifIpProcessed = 1;
				}
				if (ifIpProcessed == 1) {
					var ipSegments = ip.split('.');
					var newDomainToIpArrayString = "818000010001" + clientReq.substr(16) + "c00c00010001" + "00000002" + "0004";
					for (var loop = 0; loop < ipSegments.length; loop++) {
						var tempIpSegmentInHex = parseInt(ipSegments[loop]).toString(16);
						newDomainToIpArrayString = newDomainToIpArrayString + ("00" + tempIpSegmentInHex).substr(tempIpSegmentInHex.length);
					}
					domainToIpArray[domainNameInHex]['dnsPacketInHexWithoutTransactionId'] = newDomainToIpArrayString;
				}

*/