var fs = require('fs');
var http = require('http');

var domain = "fbcdn-profile-a.akamaihd.net";
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
						if (map_object_name_list[i].substr(0, 28) === domain) {
							if (map_object_name_list[i].length == 29) {
								dns_type = "local";
							}
							else {
								dns_type = "remote";
							}
							var dns_ip = json_data.dump.map[map_object_name_list[i]].dns;
							http_object_name_list = Object.keys(json_data.dump.map[map_object_name_list[i]]);
							for (var http_object_name_list_loop = 0; http_object_name_list_loop < http_object_name_list.length; http_object_name_list_loop++) {
								if (http_object_name_list[http_object_name_list_loop].substr(0, 4) === "http") {
									var http_object = json_data.dump.map[map_object_name_list[i]][http_object_name_list[http_object_name_list_loop]];
									var http_object_length = http_object.length;
									for (var http_object_loop = 0; http_object_loop < http_object_length; http_object_loop++) {
										var is_blackhole;
										if(http_object[http_object_loop].failed == true)
											is_blackhole = "1";
										else 
											is_blackhole = "0";
										var options = {
											host: 'www.cs.montana.edu',
											path: '/~utkarsh.goel/scripts/dns/dasu_blackhole.php?client_ip=' + client_ip + '&cdn_ip=' + http_object[http_object_loop].ip + '&is_blackhole=' + is_blackhole + '&timestamp=' + http_object[http_object_loop].creationGMTTime + "&dns_ip=" + dns_ip + "&domain=" + domain + "&dns_type=" + dns_type
										};
										http.request(options).end();
										//console.log(options);
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

