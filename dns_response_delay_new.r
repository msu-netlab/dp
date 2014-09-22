http://www.google.com/?gws_rd=ssl#q=bozeman
http://www.huffingtonpost.com/
http://www.amazon.com/
https://www.facebook.com

website1<-c(3.33, 4.11, 3.18, 3.32, 4.37, 3.94, 2.40, 4.29, 4.19, 4.15, 4.30)
website2<-c(37.14, 16.22, 16.93, 14.34, 17.77, 16.67, 15.55, 19.63, 19.14, 18.80, 18.64)
website3<-c(4.71, 4.38, 4.81, 5.03, 4.51, 5.16, 4.52, 4.80, 5.04, 4.30, 4.56)
website4<-c(16.79, 6.99, 7.31, 7.10, 7.19, 7.18, 6.85, 7.96, 7.30, 7.16, 7.38)
delays<-c(0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100)

plot(delays, website1, xlab="DNS Response Delay (ms)", ylab="Webpage Load Time (s)", pch=16, lwd=2, type="o", ylim=c(0, 38), col="black")
lines(delays, website2, pch=17, lwd=2, type="o", col="red")
lines(delays, website3, pch=18, lwd=2, type="o", col="blue")
lines(delays, website4, pch=19, lwd=2, type="o", col="grey")

legend("topright", pch=c(16,17,18,19), col=c("black", "red", "blue", "grey"), legend=c("Google.com", "Huffingtonpost.com", "Amazon.com", "Facebook.com"))
