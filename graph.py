import matplotlib.pyplot as plt

# Actual annual standard deviations (%) from Statman (1987)
n = [1, 2, 4, 6, 8, 10, 20, 30, 40, 50, 100, 200, 300, 400, 500, 1000]
std_dev = [
    49.24, 37.36, 29.69, 26.64, 24.98, 23.93,
    21.68, 20.87, 20.46, 20.20, 19.69, 19.42,
    19.34, 19.29, 19.27, 19.21
]

plt.figure(figsize=(10, 6))
plt.plot(n, std_dev, marker='o', color='blue')
plt.xscale('log')
plt.xlabel('Number of Stocks in Portfolio (log scale)')
plt.ylabel('Annual Standard Deviation (%)')
plt.title('Portfolio Standard Deviation vs. Number of Stocks (Empirical Data)')
plt.grid(True)
# Set custom x-ticks for log scale
plt.xticks([10, 100, 1000], ['10', '100', '1000'])
plt.show()