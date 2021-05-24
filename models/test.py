# libraries
import numpy as np
import matplotlib.pyplot as plt

# set width of bars
barWidth = 0.25

# set heights of bars
bars1_pending = [0, 0]
bars2_active = [3, 2]
bars3_overdue = [0, 1]

_titles = ['adherente', 'activo']

# Set position of bar on X axis
r1 = np.arange(len(bars1_pending))
r2 = [x + barWidth for x in r1]
r3 = [x + barWidth for x in r2]

# Make the plot
plt.bar(r1, bars1_pending, color='#7f6d5f', width=barWidth, edgecolor='white', label='Pending')
plt.bar(r2, bars2_active, color='#557f2d', width=barWidth, edgecolor='white', label='Active')
plt.bar(r3, bars3_overdue, color='#2d7f5e', width=barWidth, edgecolor='white', label='Overdue')

# Add xticks on the middle of the group bars
plt.xlabel('group', fontweight='bold')
plt.xticks([r + barWidth for r in range(len(bars1_pending))], _titles)

# Create legend & Show graphic
plt.legend()
plt.show()