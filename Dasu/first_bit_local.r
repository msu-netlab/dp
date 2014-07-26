mean_min <- c(8.611111, 195.333333, 7.857143, 27.500000, 4.388889, 7.666667, 10.000000, 138.291667, 50.913793, 83.700000, 95.500000, 1.166667, 67.300000, 84.600000, 4.600000, 2.500000, 37.416667, 186.111111, 216.333333, 35.500000, 62.400000, 22.555556, 28.000000, 411.942778, 13.833333, 4.750000, 60.388889, 2.500000, 32.500000, 45.333333, 242.999167, 19.666667, 66.250000, 11.222222, 3.800000, 1.000000, 50.333333, 131.250000, 45.958333, 16.500000, 119.208333, 90.333333, 5.333333, 68.000000, 10.388889, 293.527778, 6.333333, 13.700000, 171.166667, 2.500000, 55.333333, 440.996667, 415.584706, 0.000000, 318.665000, 88.833333, 33.000000, 527.830833, 61.629630, 124.333333, 26.750000, 3.750000, 10.384615, 21.055556, 2.166667, 38.119048, 10.666667, 51.666667, 28.464286, 19.000000, 15.628571, 56.805556, 18.333333, 5.083333, 113.247476, 45.441176, 76.166667, 18.166667, 65.166667, 145.666667, 64.687500, 181.000000, 64.000000, 6.500000, 76.666667, 74.333333, 309.831667, 15.000000, 16.500000, 78.958333, 27.066667, 9.272727, 19.833333, 65.833333, 120.833333)

max_min <- c(36.00, 704.00, 183.00, 75.00, 60.00, 16.00, 25.00, 341.00, 396.00, 669.00, 346.00, 2.00, 235.00, 251.00, 23.00, 7.00, 217.00, 707.00, 608.00, 108.00, 305.00, 285.00, 197.00, 964.99, 31.00, 15.00, 343.00, 4.00, 180.00, 121.00, 865.99, 48.00, 228.00, 83.00, 16.00, 4.00, 187.00, 415.00, 750.00, 26.00, 898.00, 463.00, 14.00, 213.00, 38.00, 666.00, 17.00, 97.00, 426.00, 5.00, 153.00, 894.99, 843.99, 0.00, 925.99, 192.00, 133.00, 936.99, 415.00, 345.00, 241.00, 14.00, 82.00, 130.00, 6.00, 527.00, 31.00, 246.00, 198.00, 93.00, 331.00, 866.00, 69.00, 15.00, 813.99, 611.00, 391.00, 192.00, 285.00, 648.00, 665.00, 625.00, 197.00, 22.00, 265.00, 223.00, 939.99, 27.00, 85.00, 664.00, 284.00, 34.00, 219.00, 272.00, 305.00)

mean_min_val = ecdf(mean_min)
max_min_val = ecdf(max_min)

plot(mean_min_val, lty=1, col="red", xlab="First Bit Time (ms)", ylab="CDF", main="First Bit Time with IPs returned by Local DNS", xlim=c(0, 1000))
lines(max_min_val)

legend("bottomright",  pch =16, legend=c("(Mean - Min)", "(Max - Min)"), col=c("red", "black"))