		
		
		function evaluateIpAddress(ipList){
			if(ipList.length > 0){
				var currentIp = ipList[0];
				var responseFronIp = "";
				var tcpOpenOptions = {host: currentIp, port: 80};
				var rtt;
				var initialTcpOpenTimestamp = new Date().getTime();
				var httpHeadOptions = {method: 'HEAD', host: currentIp, port: 80, path: '/'};
				var open = net.connect(tcpOpenOptions, function() {
					var timeToTCPOpen = (new Date().getTime() - initialTcpOpenTimestamp);
					var http = require('http');
					var initialHttpHeadTimestamp;
					var httpHeadReq = http.request(httpHeadOptions, function(res) {
						var timeToHttpHead = (new Date().getTime() - initialHttpHeadTimestamp);
						rtt = timeToHttpHead
						httpHeadReq.destroy();
					});
					
					httpHeadReq.on('finish', function() {
						initialHttpHeadTimestamp = new Date().getTime();
					});
					
					httpHeadReq.on('error', function() {
						rtt = timeToTCPOpen;
						httpHeadReq.destroy();
					});
				
					httpHeadReq.end();
						
				});

				open.on('error', function(e) {
				
				});
		   }
		   
		}