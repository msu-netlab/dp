var fs = require('fs');
var http = require('http');

var dir = "records/";
fs.readdir(dir, function (err, files) {
	if (err) {
		throw err;
	}
	else if(files) {
		files.forEach(function(file){
			fs.readFile(dir + file, 'utf8', function (err, data) {
				if (err) {
					return console.log(err);
				}
				else if (data) {
					json_data = JSON.parse(data);
					var client_ip = json_data._clientprefix;
					var dns_type;
					map_object_name_list = Object.keys(json_data.dump.map);
					for (var i = 0; i < map_object_name_list.length; i++) {
						if (map_object_name_list[i] === "dasu_ping") {
							var ping_data = JSON.parse(json_data.dump.map[map_object_name_list[i]]);
							var ping_data_length = ping_data.length;
							for (var ping_data_loop =0; ping_data_loop < ping_data_length; ping_data_loop++) {
								if(ping_data[ping_data_loop].rtt > 0) {
									console.log("RTT: " + ping_data[ping_data_loop].rtt + " +++ IP: " + ping_data[ping_data_loop].ip);
									var options = {
											host: 'www.cs.montana.edu',
											path: '/~utkarsh.goel/scripts/dns/dasu_to_dasu_rtt.php?client_ip=' + client_ip + '&target_ip=' + ping_data[ping_data_loop].ip + '&rtt=' + ping_data[ping_data_loop].rtt
										};
									http.request(options).end();
								}
							}
						}
					}
				}
			});
		});
	}
});

