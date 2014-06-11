<?php
$dbhostname = "nl.cs.montana.edu";
$dbusername = "dns";
$dbpassword = "Database4DnsProxy";
$dbschemaname = "dns_proxy";

$con = mysql_connect($dbhostname, $dbusername, $dbpassword);
if (!$con)
{
	die('Website down for maintenance. We will be live soon.');
}
mysql_select_db($dbschemaname, $con);

$self_ip = $_POST['self_ip'];
$dns_ip = $_POST['dns_ip'];
$app_server_ip = $_POST['app_server_ip'];
$domain_name = $_POST['domain_name'];
$is_alive = $_POST['is_alive'];

$sql = "INSERT INTO host_status (self_ip, dns_ip, app_server_ip, domain_name, is_alive) VALUES('$_SERVER[REMOTE_ADDR]', '$dns_ip', '$app_server_ip', '$domain_name', $is_alive)";
if (!mysql_query ($sql,$con)) {
	die('Website down for maintenance. We will be live soon.');
}
else {
	echo "Recored.";
}
?>