tcp_open <-c(62, 31, 31, 31, 31, 31, 15, 15, 15, 15, 15, 15, 15, 15, 15, 15, 15, 15, 15, 15, 15, 15)
x_tcp_open <-c(62, 93, 124, 155, 233, 311, 326, 404, 466, 560, 654, 748, 826, 919, 1013, 1091, 1184, 1247, 1262, 1277, 1308, 1339)	

http_head <-c(94, 94, 31, 31, 31, 31, 31, 31, 31, 31, 31, 31, 31, 31, 31, 31, 31, 31, 16, 16, 16, 16)
x_http_head <-c(94, 422, 453, 500, 578, 672, 719, 813, 891, 984, 1062, 1155, 1249, 1343, 1436, 1530, 1640, 1703, 1719, 1766, 1813, 1845)


plot(x_tcp_open, tcp_open, col="black", ylim=c(0, 100), xlim=c(0, 1900), lty=1, xlab="Time (ms)", ylab="Latency of Best Server (ms)", pch=16, lwd=2, type="o")
lines(x_http_head, http_head, col="grey", lty=1, pch=17, lwd=2, type="o")

legend("topright", pch=c(16, 17, 20),legend=c("TCP Connection Setup", "HTTP Head"), col=c("black", "grey"))


IP = 63.168.61.80----TCP Open = 62 at time = 62
														IP = 63.168.61.80----HTTP Head = 94 at time = 94
IP = 63.168.61.89----TCP Open = 31 at time = 31
														IP = 63.168.61.89----HTTP Head = 328 at time = 328
IP = 63.168.61.98----TCP Open = 31 at time = 31
														IP = 63.168.61.98----HTTP Head = 31 at time = 31
IP = 63.168.61.66----TCP Open = 31 at time = 31
														IP = 63.168.61.66----HTTP Head = 47 at time = 47
IP = 63.168.61.40----TCP Open = 78 at time = 78
														IP = 63.168.61.40----HTTP Head = 78 at time = 78
IP = 63.168.61.42----TCP Open = 78 at time = 78
														IP = 63.168.61.42----HTTP Head = 94 at time = 94
IP = 63.168.61.49----TCP Open = 15 at time = 15
														IP = 63.168.61.49----HTTP Head = 47 at time = 47
IP = 63.168.61.41----TCP Open = 78 at time = 78
														IP = 63.168.61.41----HTTP Head = 94 at time = 94
IP = 63.168.61.51----TCP Open = 62 at time = 62
														IP = 63.168.61.51----HTTP Head = 78 at time = 78
IP = 63.235.20.210----TCP Open = 94 at time = 94
														IP = 63.235.20.210----HTTP Head = 93 at time = 93
IP = 63.235.20.249----TCP Open = 94 at time = 94
														IP = 63.235.20.249----HTTP Head = 78 at time = 78
																									
														
IP = 63.235.20.219----TCP Open = 94 at time = 94
														IP = 63.235.20.219----HTTP Head = 93 at time = 93
IP = 63.235.20.225----TCP Open = 78 at time = 78
														IP = 63.235.20.225----HTTP Head = 94 at time = 94
IP = 63.235.20.232----TCP Open = 93 at time = 93
														IP = 63.235.20.232----HTTP Head = 94 at time = 94              
IP = 63.235.21.16----TCP Open = 94 at time = 94
														IP = 63.235.21.16----HTTP Head = 93 at time = 93
IP = 63.235.21.25----TCP Open = 78 at time = 78
														IP = 63.235.21.25----HTTP Head = 94 at time = 94
IP = 63.235.21.35----TCP Open = 93 at time = 93
														IP = 63.235.21.35----HTTP Head = 110 at time = 110
IP = 63.235.21.33----TCP Open = 62 at time = 62
														IP = 63.235.21.33----HTTP Head = 63 at time = 63
IP = 209.124.184.134----TCP Open = 15 at time = 15
														IP = 209.124.184.134----HTTP Head = 16 at time = 16
IP = 209.124.184.135----TCP Open = 15 at time = 15
														IP = 209.124.184.135----HTTP Head = 47 at time = 47
IP = 209.124.184.142----TCP Open = 31 at time = 31
														IP = 209.124.184.142----HTTP Head = 47 at time = 47
IP = 209.124.184.143----TCP Open = 31 at time = 31
														IP = 209.124.184.143----HTTP Head = 32 at time = 32
														
														