var dgram = require("dgram");
var net =  require("net");
var raw = require ("raw-socket");

var dnsIpList = ["8.8.8.8", "208.67.222.222", "209.244.0.3"];
var server = dgram.createSocket("udp4");
server.bind(53);
var domainToIpArray = {};
var IpPerformanceArray = {};
var primaryPort = 80;
var secondaryPort = 443;
var selfIp = require('ip').address();
var portArrayInHex = ['0050', '01bb'];
console.log("Server started on " + selfIp);

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
					}
				});
			});
			
			setTimeout(function() { 
				client.close(); 
			}, 2000);
			
			client.on("message", function (msg, rinfo) {
				var freshDomainIp = parseIpFromDnsResponse(msg);		
				if(!isDnsResponseSentToClient && freshDomainIp != 0) {
					var freshDomainTtl = "00000004";
					var dnsPacketInHexWithoutTransactionId = "818000010001" + clientReq.substr(16) + "c00c00010001" + freshDomainTtl + "0004" +freshDomainIp;
					var dnsResponseToSend = dnsResponseToSendTransactionId + dnsPacketInHexWithoutTransactionId;
					domainToIpArray[domainNameInHex] = {'ip': freshDomainIp, 'ttl': freshDomainTtl, 'dnsPacketInHexWithoutTransactionId' : dnsPacketInHexWithoutTransactionId};
					setTimeout(function() {
						sendDnsResponse((dnsResponseToSendTransactionId + domainToIpArray[domainNameInHex]['dnsPacketInHexWithoutTransactionId']), clientIp, clientPort, "first DNS response");
					}, 100);
					
				}
				else if (!isDnsResponseSentToClient && freshDomainIp == 0) {
					sendDnsResponse(msg.toString('hex', 0, msg.length), clientIp, clientPort, "original DNS server");
				}
				if(freshDomainIp != 0) {
					processDnsResponse(msg);
					//evaluateIpAddressList(processDnsResponse(msg));
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
						
						evaluateIpAddress(parseInt(ip.substr(0, 2), 16) + "." + parseInt(ip.substr(2, 2), 16) + "." + parseInt(ip.substr(4, 2), 16) + "." + parseInt(ip.substr(6, 2), 16));
						//perDnsResponseIpArray.push(parseInt(ip.substr(0, 2), 16) + "." + parseInt(ip.substr(2, 2), 16) + "." + parseInt(ip.substr(4, 2), 16) + "." + parseInt(ip.substr(6, 2), 16));
					}
					loop++;
					resAfterQuery = resAfterQuery.substr(answerLength);
				}
			}
			//return perDnsResponseIpArray;
		}
		
		function evaluateIpAddressList(ipList){
			for(var loop = 0; loop < ipList.length; loop++){
				evaluateIpAddress(ipList[loop]);
		   }
		   
		}
		
		function evaluateIpAddress(currentIp) {
			var rtt = 0;
			var timeToSynAck, initialTimestamp;
			var options = { protocol: raw.Protocol.TCP };
			var socket = raw.createSocket (options);
			socket.setOption (raw.SocketLevel.IPPROTO_IP, raw.SocketOption.IP_HDRINCL, 1);
			socket.on ("close", function () {
			});
			
			socket.on ("error", function (error) {
				console.log ("RAW Socket error: " + error.toString ());
				socket.close();
			});
			
			socket.on ("message", function (buffer, source) {
				if(source === currentIp) {
					timeToSynAck = (new Date().getTime() - initialTimestamp);
					rtt = timeToSynAck;
					if(rtt < min){
						min = rtt;
						minIp = currentIp;
						console.log("Min IP: " + minIp);
						var ipSegments = minIp.split('.');
						var newDomainToIpArrayString = "818000010001" + clientReq.substr(16) + "c00c00010001" + "00000004" + "0004";
						for (var loop = 0; loop < ipSegments.length; loop++) {
							var tempIpSegmentInHex = parseInt(ipSegments[loop]).toString(16);
							newDomainToIpArrayString = newDomainToIpArrayString + ("00" + tempIpSegmentInHex).substr(tempIpSegmentInHex.length);
						}
						domainToIpArray[domainNameInHex]['dnsPacketInHexWithoutTransactionId'] = newDomainToIpArrayString;
					}
					console.log("RTT for " + currentIp + ": " + timeToSynAck);
					socket.close();
				}
			});
			
			var commonIpHeader = '4500003c5d4840004006';
			var ipHeader = commonIpHeader + calculateChecksum(commonIpHeader + '0000' + convertIpToHex(selfIp) + convertIpToHex(currentIp)) + convertIpToHex(selfIp) + convertIpToHex(currentIp);
			for (var i = 0; i < portArrayInHex.length; i++) {
				var commonTcpHeader = 'dd0f' + portArrayInHex[i] + 'f49432e60000000080022000';
				var tcpHeader = commonTcpHeader + calculateChecksum(convertIpToHex(selfIp) + convertIpToHex(currentIp) + '00060020' + commonTcpHeader + '0000' + '0000020405b40103030801010402') + '0000020405b40103030801010402';
				var finalRawPacket = ipHeader + tcpHeader;
				finalRawPacket = ("00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000" + finalRawPacket).substr(finalRawPacket.length);
				var buffer = new Buffer(finalRawPacket, 'hex');
				socket.send (buffer, 0, buffer.length, currentIp, function (error, bytes) {
					if (error) {
						console.log (error.toString ());
					} else {
						initialTimestamp = new Date().getTime();
					}
				});	
			}
		}
		
		function calculateChecksum(header) {
			var hexArray = [];
			for (var i = 0; i < header.length; i = i + 4) {
				hexArray.push(header.substr(i, 4));
			}
			var hexSum = "0000";
			for (var i = 0; i < hexArray.length; i = i + 2) {
				var sum = (parseInt(hexArray[i], 16) + parseInt(hexArray[i + 1], 16)).toString(16);
				hexSum = (parseInt(hexSum, 16) + parseInt(sum, 16)).toString(16);
			}
			var sumInBin = Hex2Bin(hexSum);
			sumInBin = ("00000000000000000000" + sumInBin).substr(sumInBin.length);
			var reducedSumInBinary = Dec2Bin(parseInt(sumInBin.substr(0, 4), 2) + parseInt(sumInBin.substr(4), 2));
			reducedSumInBinary = ("0000000000000000" + reducedSumInBinary).substr(reducedSumInBinary.length);
			var flippedSumInBinary = parseInt("1111111111111111", 2) ^ parseInt(reducedSumInBinary, 2);
			return( (Dec2Hex(flippedSumInBinary)).toString());
		}
		
		function Bin2Dec(n){if(!checkBin(n))return 0;return parseInt(n,2).toString(10)}
		
		function Hex2Bin(n){if(!checkHex(n))return 0;return parseInt(n,16).toString(2)}
		
		function Dec2Hex(n){if(!checkDec(n)||n<0)return 0;return n.toString(16)}
		
		function checkHex(n){return/^[0-9A-Fa-f]{1,64}$/.test(n)}
		
		function checkBin(n){return/^[01]{1,64}$/.test(n)}
		
		function checkDec(n){return/^[0-9]{1,64}$/.test(n)}
		
		function Dec2Bin(n){if(!checkDec(n)||n<0)return 0;return n.toString(2)}
		
		function convertIpToHex(ip) {
			var ipInHex = '';
			var ipSegments = ip.split('.');
			for (var loop = 0; loop < ipSegments.length; loop++) {
				var tempIpSegmentInHex = parseInt(ipSegments[loop]).toString(16);
				ipInHex = ipInHex + ("00" + tempIpSegmentInHex).substr(tempIpSegmentInHex.length);
			}
			return ipInHex;
		}
		
	}
});