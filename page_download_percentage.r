without_proxy<-c(5960, 5841, 4625, 4600, 4513, 4320, 3976, 3878, 3808, 3656)

with_proxy<-c(4960, 4509, 3032, 3670, 3756, 3400, 3325, 3485, 3026, 3401)

plot(c(1:10), (((without_proxy - with_proxy) * 100)/without_proxy), col="black", type="b", ylab="Percentage (%)", xlab="No. of Websites", ylim=c(0,100), lwd=2, pch=16)

legend("topleft", legend=c("Percentage Reduction in Page Load Time"), col=c("black"), pch=16)


