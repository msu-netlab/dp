var dgram = require("dgram");
var net =  require("net");
var raw = require ("raw-socket");
var sizeof = require("object-sizeof");
var fs = require('fs');
var lineReader = require('line-reader');

var server = dgram.createSocket("udp4");
var dnsIpList = ["4.2.2.5","8.8.8.8", "208.67.222.222", "209.244.0.3"];
var domainToIpArray = {};
var selfIp = require('ip').address();
var portArrayInHex = ['0050', '01bb']; // HTTP ports 80 and 443
var cacheLimitInBytes = 10000000; // DP maximum allowable cache size
var dnsResponseDelayInMilliseconds = 40; // User configurable deadline
var defaultDnsResponseTtleInSeconds = '300';
var dnsTrafficInBytes = 0;
var tcpSynTrafficInBytes = 0;
var localSynPacketPortInHex = 'dd0f'; //port = 56591
var localSynPacketPort = 56591;
var localResolverFile = '/etc/resolv.conf';

Object.size = function(obj) { 
    var size = 0, key;
    for (key in obj) {
        if (obj.hasOwnProperty(key)) size++;
    }
    return size;
};

fs.open(localResolverFile, 'rs', function (err, data) {
	if (err) {
		console.log("File " + localResolverFile + " not Found. Moving on!!!");
	}
	else {
		lineReader.eachLine(localResolverFile, function(line, last) {
			if ((line.toLowerCase()).search("nameserver") >= 0) {
                                dnsIpList.push((line.match(/(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)/g)).toString());
                        }
		});
	}
});

server.bind(53);

server.on("error", function (err) {
        server.close();
});

server.on("listening", function () {
  	var address = server.address();
  	console.log("DNS-Proxy running on " + address.address + ":" + address.port);
});

server.on("message", function (msg, rinfo) {
	console.log("DNS Request Received.");
	var clientReq = msg.toString('hex', 0, msg.length);
	var dnsRequestType = clientReq.substr(clientReq.length - 8, 4);
	if(dnsRequestType === "0001" || dnsRequestType === "001c") {
		var min = Number.MAX_VALUE, minIp = "";
		var domainNameInHex = clientReq.substr(24, clientReq.length - 32);
		var clientIp = rinfo.address;
		var clientPort = rinfo.port;
		var isDnsResponseSentToClient = false;
		var dnsResponseToSendTransactionId = clientReq.substr(0, 4);
		var ipArray = [];
		
		if ((typeof domainToIpArray[domainNameInHex] === "undefined" && dnsRequestType === "0001") || dnsRequestType === "001c") {
			var message = new Buffer(msg);
			var client = dgram.createSocket("udp4");

			client.on('error', function(err) {
				console.log(err.toString());
			});
			
			client.bind();
			
			dnsIpList.forEach(function(dnsIp) {
				client.send(message, 0, message.length, 53, dnsIp, function(err, bytes) {
					if (err) {
						console.log(err.toString());
					}
					else if(bytes) {
						dnsTrafficInBytes = dnsTrafficInBytes + message.length + 28;
					}
				});
			});
			
			setTimeout(function() { 
				client.close(); 
			}, 2000);
			
			client.on("message", function (msg, rinfo) {
				dnsTrafficInBytes = dnsTrafficInBytes + msg.length + 28;
				var freshDomainIp = parseIpFromDnsResponse(msg);		
				if(!isDnsResponseSentToClient && freshDomainIp != 0) {
					var freshDomainTtl = "00000004";
					var dnsPacketInHexWithoutTransactionId = "818000010001" + clientReq.substr(16) + "c00c00010001" + freshDomainTtl + "0004" +freshDomainIp;
					var dnsResponseToSend = dnsResponseToSendTransactionId + dnsPacketInHexWithoutTransactionId;
					if (sizeof(domainToIpArray) + 500 <= cacheLimitInBytes) {
						domainToIpArray[domainNameInHex] = {'ttl' : defaultDnsResponseTtleInSeconds, 'dnsPacketInHexWithoutTransactionId' : dnsPacketInHexWithoutTransactionId, 'lastUsed': new Date().getTime()};
					}
					else {
						removeLeastRecentlyUsedDomainFromCache();
						domainToIpArray[domainNameInHex] = {'ttl' : defaultDnsResponseTtleInSeconds, 'dnsPacketInHexWithoutTransactionId' : dnsPacketInHexWithoutTransactionId, 'lastUsed': new Date().getTime()};
					}
					setTimeout(function() {
						if(typeof domainToIpArray[domainNameInHex] !== "undefined")
							sendDnsResponse((dnsResponseToSendTransactionId + domainToIpArray[domainNameInHex]['dnsPacketInHexWithoutTransactionId']), clientIp, clientPort, "cold cache");
					}, dnsResponseDelayInMilliseconds);
				}
				else if (!isDnsResponseSentToClient && freshDomainIp == 0) {
					sendDnsResponse(msg.toString('hex', 0, msg.length), clientIp, clientPort, "original DNS server");
				}
				if (freshDomainIp != 0) {
					processDnsResponse(msg);
				}
			});
		
		}
		else {
			var dnsResponseFromCache = dnsResponseToSendTransactionId + domainToIpArray[domainNameInHex]['dnsPacketInHexWithoutTransactionId'];
			sendDnsResponse(dnsResponseFromCache, clientIp, clientPort, "warm cache");
			domainToIpArray[domainNameInHex]['lastUsed'] = new Date().getTime();
		}
		
		function removeLeastRecentlyUsedDomainFromCache () {
			var domainNameList = Object.getOwnPropertyNames(domainToIpArray);
			var leastUsedDomainTimestamp = parseInt(domainToIpArray[domainNameList[0]]['lastUsed']);
			var leastUsedDomainIndex = 0;
			for ( var i = 0; i < domainNameList.length; i++) {
				if (parseInt(domainToIpArray[domainNameList[i]]['lastUsed']) < leastUsedDomainTimestamp) {
					leastUsedDomainTimestamp = parseInt(domainToIpArray[domainNameList[i]]['lastUsed']);
					leastUsedDomainIndex = i;
				}
			}
			delete domainToIpArray[domainNameList[leastUsedDomainIndex]];
		}
		
		function parseIpFromDnsResponse(msg) {
			var resInString = msg.toString('hex', 0 , msg.length);
			var isAuthority = parseInt(resInString.substr(16, 4), 16);
			var newResponse = resInString + "";
			if (!isAuthority || dnsRequestType === "0001") {
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
				return 0;
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
						console.log(err.toString());
					}
					else if (bytes) {
						if (responseType === "cold cache" && isDnsResponseSentToClient === false) {
							setTimeout(function() {
								delete domainToIpArray[domainNameInHex];
							}, parseInt(domainToIpArray[domainNameInHex]['ttl']) * 1000 * 8);
						}
						isDnsResponseSentToClient = true;
					}			
				});
			}
			catch (exception) {}
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
						evaluateIpAddress((parseInt(ip.substr(0, 2), 16) + "." + parseInt(ip.substr(2, 2), 16) + "." + parseInt(ip.substr(4, 2), 16) + "." + parseInt(ip.substr(6, 2), 16)), (parseInt(ipTtl, 16)).toString());
					}
					loop++;
					resAfterQuery = resAfterQuery.substr(answerLength);
				}
			}
		}
		
		function evaluateIpAddress(currentIp, ttl) {
			var rtt = 0;
			var timeToSynAck, initialTimestamp;
			var options = { protocol: raw.Protocol.TCP };
			var socket = raw.createSocket (options);
			socket.setOption (raw.SocketLevel.IPPROTO_IP, raw.SocketOption.IP_HDRINCL, 1);
			socket.on ("close", function () {
			});
			
			socket.on ("error", function (error) {
				socket.close();
			});
			
			socket.on ("message", function (buffer, source) {
				var synAckpacket = buffer.toString('hex', 0, buffer.length);
				if(source === currentIp && parseInt(synAckpacket.substr(44, 4), 16) == localSynPacketPort && (parseInt(synAckpacket.substr(40, 4), 16) == 80 || parseInt(synAckpacket.substr(40, 4), 16) == 443)) {
					timeToSynAck = (new Date().getTime() - initialTimestamp);
					rtt = timeToSynAck;
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
						domainToIpArray[domainNameInHex]['lastUsed'] = new Date().getTime();
						domainToIpArray[domainNameInHex]['ttl'] = ttl;
					}
					tcpSynTrafficInBytes = tcpSynTrafficInBytes + buffer.length;
					socket.close();
				}
			});
			
			var commonIpHeader = '4500003c5d4840004006';
			var ipHeader = commonIpHeader + calculateChecksum(commonIpHeader + '0000' + convertIpToHex(selfIp) + convertIpToHex(currentIp)) + convertIpToHex(selfIp) + convertIpToHex(currentIp);
			for (var i = 0; i < portArrayInHex.length; i++) {
				var commonTcpHeader = localSynPacketPortInHex + portArrayInHex[i] + 'f49432e60000000080022000';
				var tcpHeader = commonTcpHeader + calculateChecksum(convertIpToHex(selfIp) + convertIpToHex(currentIp) + '00060020' + commonTcpHeader + '0000' + '0000020405b40103030801010402') + '0000020405b40103030801010402';
				var finalRawPacket = ipHeader + tcpHeader;
				finalRawPacket = ("00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000" + finalRawPacket).substr(finalRawPacket.length);
				var buffer = new Buffer(finalRawPacket, 'hex');
				socket.send (buffer, 0, buffer.length, currentIp, function (error, bytes) {
					if (error) {} 
					else {
						initialTimestamp = new Date().getTime();
						tcpSynTrafficInBytes = tcpSynTrafficInBytes + buffer.length;
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
