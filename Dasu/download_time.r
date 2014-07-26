mean_min <- c(6.611111, 86.138889, 171.662921, 32.388889, 71.659091, 130.750000, 5.666667, 49.083333, 198.316667, 29.500000, 83.078740, 57.138889, 121.416667, 18.500000, 416.545500, 279.090909, 259.845000, 3.444444, 61.291667, 0.363636, 0.000000, 46.250000, 26.272727, 102.632667, 92.166667, 97.951889, 480.014792, 20.583333, 10.166667, 25.142857, 3.000000, 79.458333, 37.333333, 218.610000, 133.638889, 0.000000, 222.660000, 465.497333, 202.906667, 22.000000, 30.777778, 167.249167, 299.166000, 33.486111, 26.944444, 42.283333, 135.055556, 26.333333, 401.608889, 35.812500, 318.594103, 677.926667, 22.652778, 249.999167, 26.833333, 295.387778, 406.196333, 0.000000, 0.000000, 366.798667, 53.500000, 663.859333, 210.906467, 174.388333, 148.633000, 11.325000, 69.953908, 28.925926, 2.833333, 62.723298, 34.916667, 96.833333, 0.835616, 32.750000, 35.440417, 49.650794, 59.092593, 0.000000, 238.698333, 668.861220, 105.705633, 160.036852, 49.625000, 206.777778, 333.940588, 19.550725, 76.138889, 52.722222, 95.333333, 104.083333, 32.500000, 196.277222, 16.333333, 65.250000, 133.222222, 80.303030, 20.800000, 598.139524, 444.329444, 438.539167)

max_min <- c(21.00, 687.00, 652.00, 50.00, 830.00, 388.00, 31.00, 152.00, 581.00, 100.00, 803.00, 539.00, 282.00, 42.00, 566.99, 533.00, 413.99, 7.00, 428.00, 7.00, 0.00, 175.00, 90.00, 829.99, 922.00, 187.99, 609.99, 180.00, 18.00, 116.00, 12.00, 570.00, 74.00, 479.99, 593.00, 0.00, 324.99, 743.99, 903.99, 78.00, 143.00, 715.99, 811.99, 725.00, 56.00, 421.00, 256.00, 142.00, 730.99, 388.00, 369.99, 969.99, 156.00, 860.99, 44.00, 670.99, 857.99, 0.00, 0.00, 791.99, 114.00, 848.99, 998.99, 836.99, 920.99, 120.00, 976.99, 201.00, 13.00, 997.99, 219.00, 755.00, 38.00, 63.00, 952.99, 390.00, 357.00, 0.00, 933.99, 995.99, 977.99, 984.99, 451.00, 735.00, 835.99, 380.00, 247.00, 525.00, 253.00, 558.00, 125.00, 930.99, 41.00, 201.00, 839.00, 382.00, 50.00, 921.99, 787.99, 817.99)

mean_min_val = ecdf(mean_min)
max_min_val = ecdf(max_min)

plot(mean_min_val, lty=1, col="red", xlab="Download Time (ms)", ylab="CDF", main="Download Time with IPs returned by all DNS", xlim=c(0, 1000))
lines(max_min_val)

legend("bottomright",  pch =16, legend=c("(Mean - Min)", "(Max - Min)"), col=c("red", "black"))

