tcp_open <-c(78, 63, 63, 63, 63, 62, 62, 62, 62, 62)
x_tcp_open <-c(78, 141, 235, 313, 391, 453, 531, 609, 687, 749)

http_head <-c(125, 124, 124, 124, 124, 124, 110, 110, 110, 110)
x_http_head <-c(125, 249, 374, 608, 842, 1107, 1217, 1435, 2418, 2668 )


plot(x_tcp_open, tcp_open, col="black", ylim=c(0, 150), xlim=c(0, 2700), lty=1, xlab="Time (ms)", ylab="Latency of Best Server (ms)", main="TCP Open vs HTTP HEAD Latency Comparison for Google", pch=16, lwd=2, type="o")
lines(x_http_head, http_head, col="grey", lty=1, pch=17, lwd=2, type="o")
legend("topright", pch=c(16, 17, 18),legend=c("TCP Connection Setup", "HTTP Head"), col=c("black", "grey"))

IP = 173.194.33.121----TCP Open = 78 at time = 78
															IP = 173.194.33.121----HTTP Head = 125 at time = 125
IP = 173.194.33.109----TCP Open = 63 at time = 63
															IP = 173.194.33.109----HTTP Head = 124 at time = 124
IP = 173.194.33.122----TCP Open = 94 at time = 94
															IP = 173.194.33.122----HTTP Head = 125 at time = 125
IP = 173.194.115.45----TCP Open = 78 at time = 78
															IP = 173.194.115.45----HTTP Head = 234 at time = 234
IP = 173.194.115.58----TCP Open = 78 at time = 78
															IP = 173.194.115.58----HTTP Head = 234 at time = 234
IP = 173.194.115.57----TCP Open = 62 at time = 62
															IP = 173.194.115.57----HTTP Head = 265 at time = 265
IP = 64.233.182.155----TCP Open = 78 at time = 78
															IP = 64.233.182.155----HTTP Head = 110 at time = 110
IP = 64.233.182.157----TCP Open = 78 at time = 78
															IP = 64.233.182.157----HTTP Head = 218 at time = 218
IP = 64.233.182.154----TCP Open = 78 at time = 78
															IP = 64.233.182.154----HTTP Head = 983 at time = 983
IP = 64.233.182.156----TCP Open = 62 at time = 62
															IP = 64.233.182.156----HTTP Head = 250 at time = 250