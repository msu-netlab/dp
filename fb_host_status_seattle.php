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

$self_ip = $_GET['self_ip'];
$app_server_ip = $_GET['app_server_ip'];
$exp_time = time();
$is_alive = $_GET['is_alive'];
$is_blocked = $_GET['is_blocked'];
$self_ip_country = file_get_contents("http://ipinfo.io/$self_ip/country");
$app_server_ip_country = file_get_contents("http://ipinfo.io/$app_server_ip/country");
$domain = $_GET['domain'];

$tcp_connection_start_time = $_GET['tcp_connection_start_time'];
$tcp_connection_end_time = $_GET['tcp_connection_end_time'];
$time_first_bit_first_head =$_GET['time_first_bit_first_head'];
$time_last_bit_first_head = $_GET['time_last_bit_first_head'];
$time_first_bit_second_head =$_GET['time_first_bit_second_head'];
$time_last_bit_second_head = $_GET['time_last_bit_second_head'];
$time_first_bit_get = $_GET['time_first_bit_get'];
$time_last_bit_get = $_GET['time_last_bit_get'];

$sql = "INSERT INTO fb_cache_seattle (self_ip, app_server_ip, exp_time, is_alive, is_blocked, self_ip_country, app_server_ip_country, domain, tcp_connection_start_time, tcp_connection_end_time, time_first_bit_first_head, time_last_bit_first_head, time_first_bit_second_head, time_last_bit_second_head, time_first_bit_get, time_last_bit_get) VALUES ('$self_ip', '$app_server_ip', '$exp_time', '$is_alive', '$is_blocked', '$self_ip_country', '$app_server_ip_country', '$domain', '$tcp_connection_start_time', '$tcp_connection_end_time', '$time_first_bit_first_head', '$time_last_bit_first_head', '$time_first_bit_second_head', '$time_last_bit_second_head', '$time_first_bit_get', '$time_last_bit_get')";
echo $sql;
if (!mysql_query ($sql,$con)) {
	die('Website down for maintenance. We will be live soon.');
}
else {
	echo "Recored.";
}
?>