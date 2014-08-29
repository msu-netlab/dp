without_proxy<-c(5960, 5841, 4625, 4600, 4513, 4320, 3976, 3878, 3808, 3656)

with_proxy<-c(4960, 4509, 3032, 3670, 3756, 3400, 3325, 3485, 3026, 3401)

plot(c(1:10), without_proxy/1000, col="176", type="b", ylab="Page Load Time (s)", xlab="No. of Websites", ylim=c(0, 6), lwd=2, pch=16)
lines(c(1:10), with_proxy/1000, type="b", col="black", lwd=2, pch=17)

legend("topright", pch=c(16, 17), legend=c("Latency without DNS-Proxy", "Latency with DNS-Proxy"), col=c("176", "black"))


