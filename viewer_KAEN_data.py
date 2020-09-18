import matplotlib.pyplot as plt
import json
import statistics

path = 'c:/work/Data/2020.09.14(Poly)/'
group_count = 8
ch_count = 2

front_threshold = 130  # mV

boards = [0]  # boards to be processed
channels = [0, 1, 2, 3, 4, 5]  # channels to be processed
invert = []  # channels to be inverted

shotn = 238
shot_folder = '%s%05d' % (path, shotn)


def find_rising(signal, is_trigger):
    '''if is_trigger:
        local_threshold = trigger_threshold
    else:'''
    local_threshold = front_threshold
    for i in range(len(signal) - 1):
        if signal[i + 1] >= local_threshold > signal[i]:
            return i + (local_threshold - signal[i]) / (signal[i + 1] - signal[i])
        if signal[i + 1] <= -local_threshold < signal[i]:
            return i - (local_threshold + signal[i]) / (signal[i + 1] - signal[i])
    return -1


with open('%s/header.json' % shot_folder, 'r') as header:
    data = json.load(header)
    # board_count = len(data['boards'])
    freq = float(data['frequency'])  # GS/s
    time_step = 1 / freq  # nanoseconds
    event_len = data['eventLength']
    trigger_threshold = data['triggerThreshold']
    timeline_prototype = [0]
    while len(timeline_prototype) != event_len:
        timeline_prototype.append(timeline_prototype[-1] + time_step)

shifted = {}
sum_waveform = {}
control_timeline = [0] * 1400
number_elem = 0
for board_idx in boards:
    with open('%s/%d.json' % (shot_folder, board_idx), 'r') as board_file:
        data = json.load(board_file)
    print('board %d recorded %d events' % (board_idx, len(data)))
    sum_waveform[board_idx] = {}
    for ch in channels:
        sum_waveform[board_idx][ch] = [0] * 1400
    ax1 = plt.subplot(len(boards), 1, boards.index(board_idx) + 1)
    shifted[board_idx] = []
    for event in data:
        shifted_event = {
            'timeline': [],
            'channels': {},
            'fronts': {}
        }
        local_timeline = timeline_prototype.copy()
        start_timeline = timeline_prototype.copy()
        for group_idx in range(group_count):
        #for group_idx in range(1):
            for ch_idx in range(ch_count):
            #for ch_idx in range(1):
                ch_num = ch_idx + group_idx * 2
                if ch_num not in channels:
                    continue
                shifted_event['channels'][ch_num] = []
                if ch_num == 0:
                    front = find_rising(event['groups'][group_idx]['data'][ch_idx], True)
                    for i in range(len(local_timeline)):
                        local_timeline[i] -= front * time_step
                        start_timeline[i] -= front * time_step
                        shifted_event['timeline'].append(start_timeline[i])
                        if (local_timeline[i] * 1000) // 10 / 100 == 0:
                            index_difference = i
                    delta_t = int((200 + local_timeline[0]) / 0.3125)
                    #print(len(local_timeline))
                    #print(delta_t)
                    local_timeline = [i / 10000 for i in range(-2000000, int(local_timeline[0] * 10000), 3125)] + local_timeline
                    #print(len(local_timeline))
                    #print(index_difference)
                    shifted_event['fronts'][ch_num] = front * time_step

                    '''print('min = %.3f, max = %.3f' %
                          (min(event['groups'][group_idx]['data'][ch_idx]),
                           max(event['groups'][group_idx]['data'][ch_idx])))'''

                else:
                    front = find_rising(event['groups'][group_idx]['data'][ch_idx], False)
                    #front = find_rising(event['groups'][4]['data'][0], False)
                    shifted_event['fronts'][ch_num] = front * time_step
                for i in range(1024):
                    if ch_num in invert:
                        shifted_event['channels'][ch_num].append(-event['groups'][group_idx]['data'][ch_idx][i])

                        sum_waveform[board_idx][ch_num][i + delta_t] += -event['groups'][group_idx]['data'][ch_idx][i]
                        #control_timeline[i + delta_t] += local_timeline[i]
                        number_elem += 1
                    else:
                        shifted_event['channels'][ch_num].append(event['groups'][group_idx]['data'][ch_idx][i])
                        sum_waveform[board_idx][ch_num][i + delta_t] += event['groups'][group_idx]['data'][ch_idx][i]
                        #control_timeline[i - index_difference] += local_timeline[i]
                for i in range(delta_t):
                    sum_waveform[board_idx][ch_num][i] += 100
                for i in range(delta_t + 1024, 1400):
                    sum_waveform[board_idx][ch_num][i] += 100
                local_timeline = local_timeline + [i / 10000 for i in range(int((local_timeline[-1] + 0.3125) * 10000), (1400 - len(local_timeline)) * 3125 + int((local_timeline[-1] + 0.3125) * 10000), 3125)]
                for i in range(1400):
                    control_timeline[i] += local_timeline[i]
                        #number_elem += 1
                plt.plot(start_timeline, shifted_event['channels'][ch_num])

        shifted[board_idx].append(shifted_event)
        plt.ylabel('signal, mV')
        plt.xlabel('timeline, ns')
        plt.title('Poly 1')

'''
print('writing file...')
with open('%s/shifted.csv' % shot_folder, 'w') as shifted_file:
    line = ''
    for board_idx in boards:
        line += 't, '
        for ch in channels:
            line += 'b%dch%d, ' % (board_idx, ch)
    shifted_file.write(line[:-2] + '\n')
    for event in range(len(shifted[boards[0]])):
        for cell_idx in range(len(timeline_prototype)):
            line = ''
            for board_idx in boards:
                line += '%.4f, ' % shifted[board_idx][event]['timeline'][cell_idx]
                for ch in channels:
                    line += '%.2f, ' % shifted[board_idx][event]['channels'][ch][cell_idx]
            shifted_file.write(line[:-2] + '\n')

with open('%s/fronts.csv' % shot_folder, 'w') as fronts_file:
    line = ''
    for board_idx in boards:
        for ch in channels:
            line += 'b%dch%d, ' % (board_idx, ch)
    fronts_file.write(line[:-2] + '\n')
    for event in range(len(shifted[boards[0]])):
        line = ''
        for board_idx in boards:
            for ch in channels:
                line += '%.2f, ' % shifted[board_idx][event]['fronts'][ch]
        fronts_file.write(line[:-2] + '\n')

for board_idx in boards:
    print("board %d", board_idx)
    for ch in channels:
        if ch == 0:
            continue
        dt = [shifted[board_idx][event]['fronts'][ch] - shifted[board_idx][event]['fronts'][0]
              for event in range(len(shifted[boards[0]]))]
        print("ch %d, mean = %.3f, std = %.2f, ptp = %.2f" %
              (ch, sum(dt) / len(dt), statistics.stdev(dt), max(dt) - min(dt)))

'''
print('OK')
plt.savefig('without_aver.png')

plt.show()

#local_timeline = local_timeline + [0] * (1400 - len(local_timeline))
for board_idx in boards:
    ax2 = plt.subplot(len(boards), 1, boards.index(board_idx) + 1)
    for i in range(len(control_timeline)):
        control_timeline[i] = control_timeline[i] / len(data) / 6
    for ch in channels:
        #for i in range(200, 600):
        #base_line = sum(sum_waveform[board_idx][ch][200:600]) / len(sum_waveform[board_idx][ch][200:600])
        for i in range(len(sum_waveform[board_idx][ch])):
            sum_waveform[board_idx][ch][i] = sum_waveform[board_idx][ch][i] / len(data)
        base_line = sum(sum_waveform[board_idx][ch][200:600]) / len(sum_waveform[board_idx][ch][200:600])
        for i in range(len(sum_waveform[board_idx][ch])):
            sum_waveform[board_idx][ch][i] = sum_waveform[board_idx][ch][i] - base_line
        plt.plot(control_timeline, sum_waveform[board_idx][ch], label='Channel' + str(ch + 1))
        plt.ylabel('signal, mV')
        plt.xlabel('timeline, ns')
        plt.title('Poly 1')
        plt.legend()


plt.savefig('with_aver.png')

plt.show()

