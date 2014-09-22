http://nodejs.org/api/http.html
http://jsbin.com/
http://www.w3schools.com/
http://jsfiddle.net/
http://wordpress.org/

website1<-c(2.16, 1.63, 1.61, 2.03, 2.09, 2.31)
website2<-c(5.61, 4.85, 5.66, 5.21, 5.39, 4.65)
website3<-c(2.56, 2.22, 2.53, 2.05, 2.36, 2.72)
website4<-c(4.96, 4.46, 4.45, 4.42, 4.41, 4.38)
website5<-c(2.98, 2.88, 3.00, 3.12, 3.04, 3.23)
delays<-c(0, 20, 40, 60, 80, 100)

plot(delays, website1, xlab="DNS Response Delay (ms)", ylab="Webpage Load Time (s)", pch=16, lwd=2, type="o", ylim=c(0, 6), col="black")
lines(delays, website2, pch=17, lwd=2, type="o", col="red")
lines(delays, website3, pch=18, lwd=2, type="o", col="blue")
lines(delays, website4, pch=19, lwd=2, type="o", col="grey")
lines(delays, website5, pch=20, lwd=2, type="o", col="green")

legend("bottomright", pch=c(16,17,18,19,20), col=c("black", "red", "blue", "grey", "green"), legend=c("Nodejs.org", "Jsbin,com", "W3schools.com", "Jsfiddle.net", "wordpress.org"))
