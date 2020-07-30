import OSC_DCO7054B
import matplotlib.pyplot as plt

osc = OSC_DCO7054B.Osc('192.168.10.104')
try:
    OSC_DCO7054B.Osc.set_data_scale(osc, 1, 250)
    OSC_DCO7054B.Osc.trigger_set(osc, 1, 0.5)
    OSC_DCO7054B.Osc.set_offset(osc, 1, 500)
    time, data = OSC_DCO7054B.Osc.get_data(osc, 1)
except:
    print('No signal in this channell')
plt.plot(time, data)
plt.show()
print('end')