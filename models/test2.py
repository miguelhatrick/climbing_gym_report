# libraries
import numpy as np
import matplotlib.pyplot as plt

# set width of bars
barWidth = 0.25

# set heights of bars
bars1_pending = [0, 0]
bars2_active = [5, 2]
bars3_overdue = [0, 1]

_titles = ['adherente', 'activo']

# Heights of bars1 + bars2
bars = np.add(bars1_pending, bars2_active).tolist()

# The position of the bars on the x-axis
r = range(0, len(_titles))

# Names of group and bar width

barWidth = 1

# Create brown bars
plt.bar(r, bars1_pending, color='#afba2f', edgecolor='white', width=barWidth, label=_('Pending'))
# Create green bars (middle), on top of the first ones
plt.bar(r, bars2_active, bottom=bars1_pending, color='#557f2d', edgecolor='white', width=barWidth, label=_('Active'))
# Create green bars (top)
plt.bar(r, bars3_overdue, bottom=bars, color='#b8312a', edgecolor='white', width=barWidth, label=_('Overdue'))

# Custom X axis
plt.xticks(r, _titles, fontweight='bold')
plt.xlabel("Membership")

plt.legend()



# Show graphic
plt.show()