import matplotlib.pyplot as plt
import json
import statistics

path = 'c:/work/Data/2020.09.14(Poly)/'
group_count = 8
ch_count = 2

front_threshold = 300  # mV

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
control_timeline = [0] * 2000
number_elem = 0
for board_idx in boards:
    with open('%s/%d.json' % (shot_folder, board_idx), 'r') as board_file:
        data = json.load(board_file)
    print('board %d recorded %d events' % (board_idx, len(data)))
    sum_waveform[board_idx] = {}
    for ch in channels:
        sum_waveform[board_idx][ch] = [0] * 2000

    fig = plt.figure()
    ax1 = fig.add_subplot(111)
    #ax2 = fig.add_subplot(122)
    shifted[board_idx] = []
    for event in data[501:502]:
        shifted_event = {
            'timeline': [],
            'channels': {},
            'fronts': {}
        }
        local_timeline = timeline_prototype.copy()
        start_timeline = timeline_prototype.copy()
        #for group_idx in range(group_count):
        for group_idx in [0, 1, 2]:
            #for ch_idx in range(ch_count):
            for ch_idx in [0, 1]:
                ch_num = ch_idx + group_idx * 2
                if ch_num not in channels:
                    continue
                shifted_event['channels'][ch_num] = []
                if ch_num == 0:
                    #front = find_rising(event['groups'][group_idx]['data'][ch_idx], True)
                    front = find_rising(event['groups'][1]['data'][1], True)
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
                for i in range(delta_t + 1024, 2000):
                    sum_waveform[board_idx][ch_num][i] += 100
                local_timeline = local_timeline + [i / 10000 for i in range(int((local_timeline[-1] + 0.3125) * 10000), (2000 - len(local_timeline)) * 3125 + int((local_timeline[-1] + 0.3125) * 10000), 3125)]
                for i in range(2000):
                    control_timeline[i] += local_timeline[i]
                        #number_elem += 1
                if ch_num == 3:
                    ax1.plot(start_timeline, shifted_event['channels'][ch_num])
                    with open('ch_4.txt', 'w') as f:
                        for item in shifted_event['channels'][ch_num]:
                            f.write("%s\n" % item)
                    with open('ch_4_time.txt', 'w') as f:
                        for item in start_timeline:
                            f.write("%s\n" % item)
                    #ax2.plot(start_timeline, shifted_event['channels'][ch_num], alpha=0.05)
                    mean_base = sum(shifted_event['channels'][ch_num][0:400]) / len(shifted_event['channels'][ch_num][0:400])
                    first_std = 0
                    for base_element in shifted_event['channels'][ch_num]:
                        first_std += (base_element - mean_base) ** 2
                    std = (first_std / len(shifted_event['channels'][ch_num])) ** 0.5
                    ptp = max(shifted_event['channels'][ch_num][0:400]) - min(shifted_event['channels'][ch_num][0:400])
                    print(std, ptp)
                    print(max(shifted_event['channels'][ch_num]))
                    #index_max_one = shifted_event['channels'][ch_num].index(max(shifted_event['channels'][ch_num]))
                    #front_index = 0
                    '''for i in range(200, index_max_one):
                        if shifted_event['channels'][ch_num][i - 1] < shifted_event['channels'][ch_num][index_max_one] * 0.5 + mean_base <= \
                                shifted_event['channels'][ch_num][i]:
                            half1_index = i
                        print(shifted_event['channels'][ch_num][i - 1], shifted_event['channels'][ch_num][index_max_one] * 0.1, shifted_event['channels'][ch_num][i])
                        if shifted_event['channels'][ch_num][i - 1] < shifted_event['channels'][ch_num][index_max_one] * 0.1 + mean_base <= \
                                shifted_event['channels'][ch_num][i]:
                            front_index = i
                        if shifted_event['channels'][ch_num][i - 1] < shifted_event['channels'][ch_num][index_max_one] * 0.9 + mean_base <= \
                                shifted_event['channels'][ch_num][i]:
                            top_front_index = i'''
                    '''for i in range(index_max_one, len(shifted_event['channels'][ch_num]) - 1):
                        if shifted_event['channels'][ch_num][i + 1] < shifted_event['channels'][ch_num][index_max_one] * 0.5 + mean_base <= \
                                shifted_event['channels'][ch_num][i]:
                            half2_index = i
                        if shifted_event['channels'][ch_num][i + 1] < shifted_event['channels'][ch_num][index_max_one] * 0.1 + mean_base <= \
                                shifted_event['channels'][ch_num][i]:
                            front_index_2 = i
                        print(shifted_event['channels'][ch_num][i + 1],
                              shifted_event['channels'][ch_num][index_max_one] * 0.9,
                              shifted_event['channels'][ch_num][i])
                        if shifted_event['channels'][ch_num][i + 1] < shifted_event['channels'][ch_num][index_max_one] * 0.9 + mean_base <= \
                                shifted_event['channels'][ch_num][i]:
                            top_front_index_2 = i'''
                    #FWHM_y = (shifted_event['channels'][ch_num][half1_index] - shifted_event['channels'][ch_num][half2_index]) / 2 + shifted_event['channels'][ch_num][half2_index]
                    #FWHM = start_timeline[half2_index] - start_timeline[half1_index]
                    '''ftop_y = (shifted_event['channels'][ch_num][top_front_index] - shifted_event['channels'][ch_num][top_front_index_2]) / 2 + shifted_event['channels'][ch_num][top_front_index_2]
                    ftop = start_timeline[top_front_index_2] - start_timeline[top_front_index]
                    fbottom_y = (shifted_event['channels'][ch_num][front_index] - shifted_event['channels'][ch_num][front_index_2]) / 2 + shifted_event['channels'][ch_num][front_index_2]
                    fbottom = start_timeline[front_index_2] - start_timeline[front_index]'''
                    #ax1.hlines(shifted_event['channels'][ch_num][half2_index], -10, 20, color='r', linewidth=10, linestyle='-')
                    #ax1.hlines(shifted_event['channels'][ch_num][half1_index], -10, 20, color='m', linestyle='--')
                    #ax1.hlines(FWHM_y, start_timeline[half1_index] - 0.1, start_timeline[half2_index] - 0.3, color='g')
                    #ax1.hlines(ftop_y, start_timeline[top_front_index], start_timeline[top_front_index_2], color='r')
                    #ax1.hlines(fbottom_y, start_timeline[front_index], start_timeline[front_index_2], color='r')





        shifted[board_idx].append(shifted_event)
        #ax1.grid()
        #fig.ylabel('signal, mV')
        #fig.xlabel('timeline, ns')
        #fig.title('Poly 1')

print('OK')
#plt.savefig('without_aver.png')

#ax2.grid()
ax1.grid()
ax1.set_title('one realize')
ax1.set_ylabel('signal, mV')
ax1.set_xlabel('timeline, ns')
ax1.set_xlim(-10, 20)
ax1.text(10, 400, 'std = ' + str(((std * 100) // 1) / 100) + '\n' + 'ptp = ' + str(((ptp * 100) // 1) / 100), bbox={'facecolor': 'white', 'edgecolor': 'black',
                                                                                                                    'boxstyle': 'round'})
#ax1.text(start_timeline[half1_index] + FWHM / 4, FWHM_y + 10, 'FWHM = ' + str(((FWHM * 100) // 1) / 100) + 'ns')
#fig.savefig('Channel_4_one.png', dpi=600)
plt.show()
plt.figure()
print('Канал, Амплитуда, Фронт, Спад, Ширина на полувысоте')
#local_timeline = local_timeline + [0] * (2000 - len(local_timeline))
for board_idx in boards:
    ax2 = plt.subplot(len(boards), 1, boards.index(board_idx) + 1)
    for i in range(len(control_timeline)):
        control_timeline[i] = control_timeline[i] / len(data) / 6
    for ch in channels:
    #for ch in [3, 4]:
        #for i in range(200, 600):
        #base_line = sum(sum_waveform[board_idx][ch][200:600]) / len(sum_waveform[board_idx][ch][200:600])
        for i in range(len(sum_waveform[board_idx][ch])):
            sum_waveform[board_idx][ch][i] = sum_waveform[board_idx][ch][i] / len(data)
        base_line = sum(sum_waveform[board_idx][ch][200:600]) / len(sum_waveform[board_idx][ch][200:600])
        for i in range(len(sum_waveform[board_idx][ch])):
            sum_waveform[board_idx][ch][i] = sum_waveform[board_idx][ch][i] - base_line
        index_max = sum_waveform[board_idx][ch].index(max(sum_waveform[board_idx][ch]))
        front_index, top_front_index = 0, 0
        last_front_index, top_last_front_index = 0, 0
        half1_index = 0
        half2_index = 0
        for i in range(600, index_max):
            if sum_waveform[board_idx][ch][i - 1] < sum_waveform[board_idx][ch][index_max] * 0.1 <= sum_waveform[board_idx][ch][i]:
                front_index = i
            if sum_waveform[board_idx][ch][i - 1] < sum_waveform[board_idx][ch][index_max] * 0.9 <= sum_waveform[board_idx][ch][i]:
                top_front_index = i
            if sum_waveform[board_idx][ch][i - 1] < sum_waveform[board_idx][ch][index_max] * 0.5 <= sum_waveform[board_idx][ch][i]:
                half1_index = i
        for i in range(index_max, len(sum_waveform[board_idx][ch]) - 1):
            if sum_waveform[board_idx][ch][i + 1] < sum_waveform[board_idx][ch][index_max] * 0.1 <= sum_waveform[board_idx][ch][i]:
                last_front_index = i
            if sum_waveform[board_idx][ch][i + 1] < sum_waveform[board_idx][ch][index_max] * 0.9 <= sum_waveform[board_idx][ch][i]:
                top_last_front_index = i
            if sum_waveform[board_idx][ch][i + 1] < sum_waveform[board_idx][ch][index_max] * 0.5 <= sum_waveform[board_idx][ch][i]:
                half2_index = i
        print(ch, max(sum_waveform[board_idx][ch]), control_timeline[top_front_index] - control_timeline[front_index],
              control_timeline[last_front_index] - control_timeline[top_last_front_index], - control_timeline[half1_index] + control_timeline[half2_index])
        #FWHM_y = (sum_waveform[board_idx][ch][half1_index] - sum_waveform[board_idx][ch][half2_index]) / 2 + sum_waveform[board_idx][ch][half2_index]
        #FWHM = control_timelin[half2_index] - control_timelin[half1_index]
        #if ch == 3:
        plt.plot(control_timeline, sum_waveform[board_idx][ch], '-', label='Channel' + str(ch + 1))
        plt.scatter(control_timeline[half1_index], sum_waveform[board_idx][ch][half1_index], color='r')
        plt.scatter(control_timeline[half2_index], sum_waveform[board_idx][ch][half2_index], color='g')
        plt.ylabel('signal, mV')
        plt.xlabel('timeline, ns')
        plt.title('Poly 1')
        plt.legend()


plt.savefig('with_aver.png')

plt.show()

