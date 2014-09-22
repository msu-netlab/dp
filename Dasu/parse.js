var fs = require('fs');
var http = require('http');

var domain = "lh3.googleusercontent.com";
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
					var dns_ping_array = {};
					for (var dns_server_loop = 0; dns_server_loop < (((json_data.dump.map.dns_servers).replace(/"/g,'')).replace(/\[|\]/g,'')).split(',').length; dns_server_loop++){
						//if (parseInt((JSON.parse(json_data.dump.map.dns_ping))[dns_server_loop].rtt) > 0) {
							dns_ping_array[(JSON.parse(json_data.dump.map.dns_ping))[dns_server_loop].ip] = (JSON.parse(json_data.dump.map.dns_ping))[dns_server_loop].rtt;
						//}
					}
					map_object_name_list = Object.keys(json_data.dump.map);
					for (var i = 0; i < map_object_name_list.length; i++) {
						if (map_object_name_list[i].substr(0, 25) === domain) {
							if (map_object_name_list[i].length == 26) {
								dns_type = "local";
							}
							else {
								dns_type = "remote";
							}
							var dns_ip = json_data.dump.map[map_object_name_list[i]].dns;
							var dns_ping = dns_ping_array[dns_ip];
							http_object_name_list = Object.keys(json_data.dump.map[map_object_name_list[i]]);
							for (var http_object_name_list_loop = 0; http_object_name_list_loop < http_object_name_list.length; http_object_name_list_loop++) {
								if (http_object_name_list[http_object_name_list_loop].substr(0, 4) === "http") {
									var http_object = json_data.dump.map[map_object_name_list[i]][http_object_name_list[http_object_name_list_loop]];
									var http_object_length = http_object.length;
									for (var http_object_loop = 0; http_object_loop < http_object_length; http_object_loop++) {
										var app_server_ip = http_object[http_object_loop].ip;
										var connection_setup_time = http_object[http_object_loop].connectTime;
										var first_bit_time = http_object[http_object_loop].recvHeadTime;
										var header_size = http_object[http_object_loop].headBytes;
										var download_time = http_object[http_object_loop].restOfBytesTime;
										var image_size = http_object[http_object_loop].objBytes;
										var options = {
											host: 'www.cs.montana.edu',
											path: '/~utkarsh.goel/scripts/dns/dasu.php?client_ip=' + client_ip + '&dns_ip=' + dns_ip + '&app_server_ip=' + app_server_ip + '&connection_setup_time=' + connection_setup_time + '&first_bit_time=' + first_bit_time + '&header_size=' + header_size + '&download_time=' + download_time + '&image_size=' + image_size + '&domain=' + domain + '&dns_type=' + dns_type + '&dns_ping=' + dns_ping
										};
										console.log(options);
										//http.request(options).end();
									}	
								}
							}
						}
					}
				}
			});
		});
	}
});

