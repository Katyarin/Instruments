import OSC_DCO7054B
import matplotlib.pyplot as plt

osc = OSC_DCO7054B.Osc('192.168.10.104')
time = {}
data = {}
try:
    for i in range(1, 5):
        time[i], data[i] = OSC_DCO7054B.Osc.get_data(osc, i)
except:
    print('No signal in this channell')

for key in data.keys():
    plt.plot(time[key], data[key])

amplitude = {}
plt.show()

plt.figure()
for key in data.keys():
    maximum = max(data[key])
    minimum = min(data[key])
    print(maximum, minimum)
    noise = (maximum - minimum) / 6 / 4
    print(noise)
    list_maxs = []
    list_mins = []
    for j in data[key]:
        if maximum - j < 2 * noise:
            list_maxs.append(j)
            edge_left = len(list_mins)
        if j - minimum < 2 * noise:
            list_mins.append(j)
    size_max = len(list_maxs)
    size_min = len(list_mins)
    print(size_min, size_max)
    del list_maxs[0:int(size_max * 0.15)]
    del list_maxs[(len(list_maxs) - int(size_max * 0.15)):]
    del list_mins[edge_left:int(edge_left + size_min * 0.15)]
    del list_mins[int(edge_left - size_min * 0.15):edge_left]
    plt.plot(list_maxs)
    plt.plot(list_mins)
    amplitude[key] = (sum(list_maxs) / len(list_maxs)) - (sum(list_mins) / len(list_mins))

print(amplitude)
plt.show()
print('end')