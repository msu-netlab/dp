var pcap = require("pcap"),
    pcap_session = pcap.createSession("", "tcp");

console.log("Listening on " + pcap_session.device_name);

pcap_session.on('packet', function (raw_packet) {
    var packet = pcap.decode.packet(raw_packet);
        console.log(packet);
		//data = packet.link.ip.tcp.data;
});