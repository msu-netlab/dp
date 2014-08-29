
var raw = require ("../");

var options = { protocol: raw.Protocol.TCP };

var socket = raw.createSocket (options);

socket.setOption (raw.SocketLevel.IPPROTO_IP, raw.SocketOption.IP_HDRINCL, 1);

socket.on ("close", function () {
	console.log ("socket closed");
	process.exit (-1);
});

socket.on ("error", function (error) {
	console.log ("error: " + error.toString ());
	process.exit (-1);
});

socket.on ("message", function (buffer, source) {
	if(source === "209.124.184.134") {
		console.log ("received " + buffer.length + " bytes from " + source);
		console.log ("data: " + buffer.toString ("hex"));
	}
});
var ipHeader = '4500003c5d4840004006432c995a76ead17cb886';
var tcpHeader = 'dd0f0050f49432e60000000080022000' + 'afed' + '0000020405b40103030801010402';
var buffer = new Buffer(ipHeader + tcpHeader, 'hex');

function ping () {
	target = "209.124.184.134";
	socket.send (buffer, 0, buffer.length, target, function (error, bytes) {
		if (error) {
			console.log (error.toString ());
		} else {
			console.log ("sent " + bytes + " bytes to " + target);
		}
	});
}

ping ();
