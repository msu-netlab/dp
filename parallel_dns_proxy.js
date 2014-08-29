var dgram = require("dgram");
var net =  require("net");

var dnsIpList = ["8.8.8.8", "208.67.222.222", "209.244.0.3"];
var server = dgram.createSocket("udp4");
server.bind(53);
var domainToIpArray = {};
var IpPerformanceArray = {};
var primaryPort = 80;
var secondaryPort = 443;

server.on("error", function (err) {
	console.log("server error:\n" + err.stack);
	server.close();
});

server.on("message", function (msg, rinfo) {
	var clientReq = msg.toString('hex', 0, msg.length);
	if(clientReq.substr(clientReq.length - 8, 4) == "0001") {
		var min = Number.MAX_VALUE, minIp = "";
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
				//ipArray = ipArray.filter (function (v, i, a) { return a.indexOf (v) == i });
				//evaluateIpAddress(ipArray, null);
			}, 2000);
			
			
			
			client.on("message", function (msg, rinfo) {
				var freshDomainIp = parseIpFromDnsResponse(msg);		
				if(!isDnsResponseSentToClient && freshDomainIp != 0) {
					var freshDomainTtl = "00000004";
					var dnsPacketInHexWithoutTransactionId = "818000010001" + clientReq.substr(16) + "c00c00010001" + freshDomainTtl + "0004" +freshDomainIp;
					var dnsResponseToSend = dnsResponseToSendTransactionId + dnsPacketInHexWithoutTransactionId;
					sendDnsResponse(dnsResponseToSend, clientIp, clientPort, "first DNS response");
					domainToIpArray[domainNameInHex] = {'ip': freshDomainIp, 'ttl': freshDomainTtl, 'dnsPacketInHexWithoutTransactionId' : dnsPacketInHexWithoutTransactionId};
				}
				else if (!isDnsResponseSentToClient && freshDomainIp == 0) {
					sendDnsResponse(msg.toString('hex', 0, msg.length), clientIp, clientPort, "original DNS server");
				}
				if(freshDomainIp != 0) {
					evaluateIpAddressList(processDnsResponse(msg));
				}
			});
		
		}
		else {
			var dnsResponseFromCache = dnsResponseToSendTransactionId + domainToIpArray[domainNameInHex]['dnsPacketInHexWithoutTransactionId'];
			sendDnsResponse(dnsResponseFromCache, clientIp, clientPort, "cache");
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

		function sendDnsResponse(msg, ip, port, responseType) {
			try { 
				var message = new Buffer(msg, 'hex');
				server.send(message, 0, message.length, port, ip, function(err, bytes) {
					if (err) {
						console.log("Error sending DNS response to client");
					}
					else if (bytes) {
						isDnsResponseSentToClient = true;
						console.log("response sent to client from " + responseType);
					}			
				});
				}
			catch (exception) {
				console.log("Malformed DNS response.");
			}
		}
		
		function processDnsResponse(msg) {
			var perDnsResponseIpArray = [];
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
						perDnsResponseIpArray.push(parseInt(ip.substr(0, 2), 16) + "." + parseInt(ip.substr(2, 2), 16) + "." + parseInt(ip.substr(4, 2), 16) + "." + parseInt(ip.substr(6, 2), 16));
					}
					loop++;
					resAfterQuery = resAfterQuery.substr(answerLength);
				}
			}
			return perDnsResponseIpArray;
		}
		
		function evaluateIpAddressList(ipList){
			for(var loop = 0; loop < ipList.length; loop++){
				evaluateIpAddress(ipList[loop]);
		   }
		   
		}
		
		function evaluateIpAddress(currentIp) {
			var responseFronIp = "";
			var tcpOpenOptions = {host: currentIp, port: primaryPort};
			var rtt;
			var httpHeadPacket = "HEAD / HTTP/1.0\r\n\r\n";
			var pointer = 0;
			var timeToHttpHead;
			var initialTcpOpenTimestamp = new Date().getTime();
			var open = net.connect(tcpOpenOptions, function() {
				pointer = 1;
				timeToTCPOpen = (new Date().getTime() - initialTcpOpenTimestamp);
				console.log("IP: " + currentIp + "====Start: " + initialTcpOpenTimestamp + "====End: " + new Date().getTime() + "====Open: " + timeToTCPOpen);
				var initialHttpHeadTimestamp;
				open.write(httpHeadPacket, function() {
					initialHttpHeadTimestamp = new Date().getTime();
					
					pointer = 2;
				});
				
				open.on('data', function(data) {
					try {
						var timeToHttpHead = (new Date().getTime() - initialHttpHeadTimestamp);
						rtt = timeToTCPOpen;
						if(rtt < min){
							min = rtt;
							minIp = currentIp;
							var ipSegments = minIp.split('.');
							var newDomainToIpArrayString = "818000010001" + clientReq.substr(16) + "c00c00010001" + "00000004" + "0004";
							for (var loop = 0; loop < ipSegments.length; loop++) {
								var tempIpSegmentInHex = parseInt(ipSegments[loop]).toString(16);
								newDomainToIpArrayString = newDomainToIpArrayString + ("00" + tempIpSegmentInHex).substr(tempIpSegmentInHex.length);
							}
							domainToIpArray[domainNameInHex]['dnsPacketInHexWithoutTransactionId'] = newDomainToIpArrayString;
						}
					}
					catch (exception) {
						console.log("Message received when socket was closed.");
					}
					open.end();
				});
						
			});
				open.on('error', function (e) {
					open.end();
				if (e.code === "ECONNRESET" && (pointer == 2 || pointer == 1)) {
					var timeToReply = (new Date().getTime() - initialTcpOpenTimestamp);
					rtt = (timeToReply)/2;
					console.log("RESET RTT for " + currentIp + ": " + rtt);
					if(rtt < min){
						min = rtt;
						minIp = currentIp;
						var ipSegments = minIp.split('.');
						var newDomainToIpArrayString = "818000010001" + clientReq.substr(16) + "c00c00010001" + "00000004" + "0004";
						for (var loop = 0; loop < ipSegments.length; loop++) {
							var tempIpSegmentInHex = parseInt(ipSegments[loop]).toString(16);
							newDomainToIpArrayString = newDomainToIpArrayString + ("00" + tempIpSegmentInHex).substr(tempIpSegmentInHex.length);
						}
						domainToIpArray[domainNameInHex]['dnsPacketInHexWithoutTransactionId'] = newDomainToIpArrayString;
					}
				}
				else if (e.code === "ECONNREFUSED" || e.code === "ETIMEDOUT") {
					var timeToReply = (new Date().getTime() - initialTcpOpenTimestamp);
					if (e.code === "ETIMEDOUT") {
						rtt = timeToReply;
						console.log("TIMEDOUT RTT for " + currentIp + ": " + rtt + " trying for port 443");
					}
					else if (e.code === "ECONNREFUSED") {
						rtt = timeToReply/3;
						console.log("CONNREFUSED RTT for " + currentIp + ": " + rtt + " trying for port 443");
					}		
					var tcpOpenOptions443 = {host: currentIp, port: secondaryPort};
					initialTcpOpenTimestamp443 = new Date().getTime();
					open443 = net.connect(tcpOpenOptions443, function() {
						var timeToTCPOpen443 = new Date().getTime() - initialTcpOpenTimestamp443;
						open443.end();
						rtt = timeToTCPOpen443;
						console.log("Connected with 443. Time to establish: " + rtt);
						if(rtt < min){
							min = rtt;
							minIp = currentIp;
							var ipSegments = minIp.split('.');
							var newDomainToIpArrayString = "818000010001" + clientReq.substr(16) + "c00c00010001" + "00000004" + "0004";
							for (var loop = 0; loop < ipSegments.length; loop++) {
								var tempIpSegmentInHex = parseInt(ipSegments[loop]).toString(16);
								newDomainToIpArrayString = newDomainToIpArrayString + ("00" + tempIpSegmentInHex).substr(tempIpSegmentInHex.length);
							}
							domainToIpArray[domainNameInHex]['dnsPacketInHexWithoutTransactionId'] = newDomainToIpArrayString;
						}
					});
					
					open443.on('error', function (e) {
						open443.end();
						if (e.code === "ETIMEDOUT") {
							var timeToReply = (new Date().getTime() - initialTcpOpenTimestamp443);
							rtt = timeToReply;
							console.log("TIMEDOUT RTT for " + currentIp + ": " + rtt + " trying for port 443");
						}
						else {
							console.log("Error from " + currentIp + " for port 443: " + e);
						}
					});
					
				}
				else {
					console.log("TCP Error for " + currentIp + ": " + e);
				}
			});
		}
		
	}
});