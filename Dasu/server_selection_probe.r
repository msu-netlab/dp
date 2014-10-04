f_tcp<-c(130.7857143, 124.9642857, 122.9285714, 122.3571429, 121.6071429, 120, 115.3571429, 92.35714286, 92.35714286, 92.07142857, 91.89285714, 91.71428571, 91.53571429, 91.53571429, 91.53571429, 91.35714286, 91.14285714, 91.14285714)
f_http<-c(152.75, 145.0357143, 126.6071429, 121.9642857, 121.6428571, 120.3928571, 118.7857143, 118.7857143, 117.3571429, 94.60714286, 93, 92.82142857, 92.64285714, 92.64285714, 92.64285714, 91.85714286, 91.85714286, 91.85714286)
x<-c(50, 70, 90, 110, 130, 150, 170, 190, 210, 230, 250, 270, 290, 310, 330, 350, 370, 390)

plot(x, f_tcp, type="o", col="grey", ylab="Download Time (ms)", xlab="Probing Delay (ms)", ylim=c(80, 165), pch=16)
lines(x, f_http, type="o", col="black", pch=17)

legend("topright", col=c("grey", "black"), pch=c(16, 17), legend=c("Based on TCP connection setup time", "Based on HTTP response time"))





g_tcp<-c(210.625, 205.58333333333, 202.95833333333, 201.875, 201.75, 201.375, 199.125, 199.125, 198.91666666667, 198.91666666667, 198.91666666667, 198.625, 198.58333333333, 198.33333333333, 197.83333333333, 197.83333333333, 197.58333333333, 197.58333333333)
g_http<-c(209.58333333333, 207.66666666667, 204.45833333333, 202.91666666667, 201.91666666667, 201.79166666667, 201.41666666667, 200.95833333333, 200.95833333333, 200.95833333333, 200.95833333333, 200.95833333333, 198.95833333333, 198.95833333333, 198.33333333333, 198.29166666667, 198.25, 197.58333333333)
x<-c(50, 70, 90, 110, 130, 150, 170, 190, 210, 230, 250, 270, 290, 310, 330, 350, 370, 390)

plot(x, g_tcp, type="o", col="grey", ylab="Download Time (ms)", xlab="Probe Delay (ms)", ylim=c(195, 215), pch=16)
lines(x, g_http, type="o", col="black", pch=17)

legend("topright", col=c("grey", "black"), pch=c(16, 17), legend=c("Based on TCP connection setup time", "Based on HTTP response time"))
