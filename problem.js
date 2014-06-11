var dns = require('native-dns'), util = require('util');
var ping = require ("net-ping");
var session = ping.createSession ();
var req;

var question = dns.Question({ name: 'pagead2.googlesyndication.com', type: 'A' });
generateDnsReq("8.8.8.8");
var start;

function generateDnsReq(dnsServer) {
	req = dns.Request({ question: question, server: dnsServer, timeout: 1000});
	req.send();
	start = new Date().getTime();
}

req.on('timeout', function () {
  console.log('Timeout in making request');
});

req.on('message', function (err, res) {
	console.log("got");
	if (res) {
		res.answer.forEach(function (a) {
			if(typeof a.address !== "undefined") {
				session.pingHost (a.address, function (error, target) {
					if (error)
						console.log ("Response from " + res._socket.address + ": " + target + ": " + error.toString ());
					else
						console.log ("Response from " + res._socket.address + ": " + target + ": Alive");
				});
			}
		});
	}
	else if (err) {
		console.log(err + "");
	}
});

req.on('end', function () {
  var delta = (new Date().getTime()) - start;
  console.log('Finished processing request: ' + delta.toString() + 'ms');
});
