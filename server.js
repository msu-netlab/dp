var dgram = require("dgram");
var server = dgram.createSocket("udp4");
server.bind(53);
var client = dgram.createSocket("udp4");
client.bind(9000);
var serverBusy = 0;
var clientAddress;
var clientPort;
var count = 0;
		
server.on("error", function (err) {
	console.log("server error:\n" + err.stack);
	server.close();
});

server.on("message", function (msg, rinfo) {
	var reqInString = msg.toString('hex',0 , msg.length);
	if(reqInString.substr(reqInString.length - 8, 4) == "0001") {
		clientAddress = rinfo.address;
		clientPort = rinfo.port;
		var message = new Buffer(msg);
			client.send(message, 0, message.length, 53, "8.8.8.8", function(err, bytes) {
				console.log("DNS request forwarded to Google's DNS");
			});
	}
});

client.on("message", function (msg, rinfo) {
	var resInString = msg.toString('hex', 0 , msg.length);
	var isAuthority = parseInt(resInString.substr(16, 4), 16);
	var newResponse = resInString + "";
	if (!isAuthority) {
		count = count + 1;
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
			var ttlInHex = answer.substr(12, 8); 
			var newTtlInDecimal = 1;
			var newTtlInHex = newTtlInDecimal.toString(16);
			var newTtlReplaceString = ("00000000" + newTtlInHex).substr(newTtlInHex.length);
			var newAnswer = answer.replace(ttlInHex, newTtlReplaceString);
			/*if(dataLength == 4 && count == 2 ) {
				var oldIp = answer.substr(answer.length -8);
				var newIp = "08080808";
				newAnswer = newAnswer.replace(oldIp, newIp);
			}*/
			newResponse = newResponse + newAnswer;
			loop++;
			resAfterQuery = resAfterQuery.substr(answerLength);
		}
	}
	
	var message = new Buffer(newResponse, 'hex');
	server.send(message, 0, message.length, clientPort, clientAddress, function(err, bytes) {
		console.log("response sent to client");
	});
});
