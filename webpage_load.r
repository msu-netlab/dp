dat <- read.table(text = "a,b,c,d
2599,705,136,141
735,1910,792,93", header = TRUE, sep=",")
barplot(as.matrix(dat), xlab="Websites and Content Delivery Networks", ylab="Reduction in Web page Load time (ms)", ylim=c(0, 3500), width=2, names.arg=c("Huffingtonpost \n Akamai", "AdultTube \n Reflected N/W", "Marvel.com \n Limelight", "Google Maps \n Google"), col=heat.colors(2))
legend(5, 3500, c("dp with cold cache", "dp with warm cache"), fill=heat.colors(2))

dat <- read.table(text = "a,b,c,d
28.8,6.6,1.3,2.6
8.2,18.1,7.6,1.2", header = TRUE, sep=",")
barplot(as.matrix(dat), xlab="Websites and Content Delivery Networks", ylab="Percentage Reduction in Web page Load time (%)", ylim=c(0, 50), width=2, names.arg=c("Huffingtonpost \n Akamai", "AdultTube \n Reflected N/W", "Marvel.com \n Limelight", "Google Maps \n Google"), col=heat.colors(2))
legend(5, 100, c("dp with cold cache", "dp with warm cache"), fill=heat.colors(2))
