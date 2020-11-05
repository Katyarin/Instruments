import matplotlib.pyplot as plt
import json
import ijson
import itertools
import os

path = 'c:/work/Data/Polychromators/2020.11.05/'
HEADER_FILE = 'header'
FILE_EXT = 'json'
board_file = None
shotn = 270
shot_folder = '%s%05d' % (path, shotn)

group_count = 8
ch_count = 2
file_num = '00' + str(shotn)
front_threshold = 500

channels = [0, 1, 2, 6, 7, 11, 12]
Poly = [i for i in range(1, 11)]
invert = []  # channels to be inverted

def get_event(shotn, board_id):
    global board_file
    shot_path = '%s%s' % (path, shotn)
    if not os.path.isdir(shot_path):
        print('Requested shotn is missing.')
        return {}
    if not os.path.isfile('%s/%d.%s' % (shot_path, board_id, FILE_EXT)):
        print('Requested shot is missing requested board file.')
        return {}
    board_file = open('%s/%d.%s' % (shot_path, board_id, FILE_EXT), 'rb')
    objects = ijson.items(board_file, 'item', use_float=True)
    return itertools.islice(objects, 0, None)

def get_shot(shotn):
    shot_path = '%s%s' % (path, shotn)
    if not os.path.isdir(shot_path):
        print('Requested shotn is missing.')
        return {}
    if not os.path.isfile('%s/%s.%s' % (shot_path, HEADER_FILE, FILE_EXT)):
        print('Requested shot is missing header file.')
        return {}
    resp = [[] for board in range(4)]
    for board_id in boards:
        if os.path.isfile('%s/%d.%s' % (shot_path, board_id, FILE_EXT)):
            with open('%s/%d.%s' % (shot_path, board_id, FILE_EXT), 'rb') as board_file:
                print('opened %d' % board_id)
                events = ijson.basic_parse(board_file, use_float=True)
                counter = 0
                for event, value in events:
                    if event == 'map_key' and value == 'timestamp':
                        event, value = events.__next__()
                        if not counter:
                            resp[board_id].append(value)
                        else:
                            if counter == 7:
                                counter = 0
                                continue
                        counter += 1
    return resp

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

boards = [0]
for element in [10]:
    n = (Poly[element] - 1) % 3
    if Poly[element] % 3 == 1:
        board += 1

sum_waveform = {}
shifted = {}
control_timeline = [0] * 2000
number_elem = 0
ch_new = [0] + [1, 2, 3, 6, 5] * 3
fig1 = plt.figure()

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

number_events = {}
timestamps = get_shot('00274')  # This reads all files to count total events.

board = 0

for element in [9]:
    n = (Poly[element] - 1) % 3
    if Poly[element] % 3 == 1:
        board += 1

    #for board in boards:
    number_events[board] = len(timestamps[board])
    print('Board %d recordered %d events.' % (board, len(timestamps[board])))

    board_idx = board
    #for board_idx in boards:
    sum_waveform[board_idx] = {}
    for ch in channels:
        sum_waveform[board_idx][ch_new[ch]] = [0] * 2000
    ax1 = fig1.add_subplot(1, 1, boards.index(board_idx) + 1)
    ax1.grid()
    # ax1.set_title(str(len(data)) + ' impulses')
    ax1.set_ylabel('signal, mV')
    ax1.set_xlabel('timeline, ns')
    ax1.set_xlim(-20, 120)
    # ax2 = fig.add_subplot(122)
    shifted[board_idx] = []

    for event in get_event(file_num, board_idx):
        shifted_event = {
            'timeline': [],
            'channels': {},
            'fronts': {}
        }

        local_timeline = timeline_prototype.copy()
        start_timeline = timeline_prototype.copy()
        for group_idx in range(group_count):
            # for group_idx in [0, 1, 2]:
            for ch_idx in range(ch_count):
                # for ch_idx in [0, 1]:
                ch_num = ch_idx + group_idx * 2
                if ch_num not in channels:
                    continue
                shifted_event['channels'][ch_num] = []
                if ch_num == 0:
                    front = find_rising(event['groups'][group_idx]['data'][ch_idx], True)
                    # front = find_rising(event['groups'][1]['data'][1], True)
                    for i in range(len(local_timeline)):
                        local_timeline[i] -= front * time_step
                        start_timeline[i] -= front * time_step
                        shifted_event['timeline'].append(start_timeline[i])
                        if (local_timeline[i] * 1000) // 10 / 100 == 0:
                            index_difference = i
                    delta_t = int((200 + local_timeline[0]) / 0.3125)
                    # print(len(local_timeline))
                    # print(delta_t)
                    local_timeline = [i / 10000 for i in
                                      range(-2000000, int(local_timeline[0] * 10000), 3125)] + local_timeline
                    # print(len(local_timeline))
                    # print(index_difference)
                    shifted_event['fronts'][ch_num] = front * time_step

                else:
                    front = find_rising(event['groups'][group_idx]['data'][ch_idx], False)
                    #front = find_rising(event['groups'][4]['data'][0], False)
                    shifted_event['fronts'][ch_num] = front * time_step
                for i in range(1024):
                    if ch_num in invert:
                        shifted_event['channels'][ch_num].append(-event['groups'][group_idx]['data'][ch_idx][i])

                        sum_waveform[board_idx][ch_new[ch_num]][i + delta_t] += -event['groups'][group_idx]['data'][ch_idx][i]
                        #control_timeline[i + delta_t] += local_timeline[i]
                        number_elem += 1
                    else:
                        shifted_event['channels'][ch_num].append(event['groups'][group_idx]['data'][ch_idx][i])
                        sum_waveform[board_idx][ch_new[ch_num]][i + delta_t] += event['groups'][group_idx]['data'][ch_idx][i]
                        #control_timeline[i - index_difference] += local_timeline[i]
                for i in range(delta_t):
                    sum_waveform[board_idx][ch_new[ch_num]][i] += 100
                for i in range(delta_t + 1024, 2000):
                    sum_waveform[board_idx][ch_new[ch_num]][i] += 100
                local_timeline = local_timeline + [i / 10000 for i in range(int((local_timeline[-1] + 0.3125) * 10000), (2000 - len(local_timeline)) * 3125 + int((local_timeline[-1] + 0.3125) * 10000), 3125)]
                for i in range(2000):
                    control_timeline[i] += local_timeline[i]
                        #number_elem += 1
                #if ch_num == 3:
                ax1.plot(start_timeline, shifted_event['channels'][ch_num])
        shifted[board_idx].append(shifted_event)

plt.savefig('270_5_11_20.png', dpi=600)
plt.show()
print('OK')

print('Канал, Амплитуда, Фронт, Спад, Ширина на полувысоте')
#local_timeline = local_timeline + [0] * (2000 - len(local_timeline))
fig2 = plt.figure()
#ax2 = fig2.add_subplot(111)
#ax2.grid()
parametrs = []
for board_idx in boards:
    ax2 = fig2.add_subplot(1, 1, boards.index(board_idx) + 1)
    ax2.grid()
    #ax2 = plt.subplot(len(boards), 1, boards.index(board_idx) + 1)
    for i in range(len(control_timeline)):
        control_timeline[i] = control_timeline[i] / number_events[board_idx]

    print(sum_waveform[board_idx].keys())
    for ch in sum_waveform[board_idx].keys():
    #for ch in [3, 4]:
        #for i in range(200, 600):
        base_line = sum(sum_waveform[board_idx][ch][200:600]) / len(sum_waveform[board_idx][ch][200:600])
        for i in range(len(sum_waveform[board_idx][ch])):
            sum_waveform[board_idx][ch][i] = sum_waveform[board_idx][ch][i] / number_events[board_idx]
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
        #ch_new = [4] + [1, 2, 3, 6, 5] * 3

        parametrs.append([ch, round(max(sum_waveform[board_idx][ch]), 2), round(control_timeline[top_front_index] - control_timeline[front_index], 2),
              round(control_timeline[last_front_index] - control_timeline[top_last_front_index], 2), round(- control_timeline[half1_index] + control_timeline[half2_index], 2)])
        print(parametrs[ch])
        #FWHM_y = (sum_waveform[board_idx][ch][half1_index] - sum_waveform[board_idx][ch][half2_index]) / 2 + sum_waveform[board_idx][ch][half2_index]
        #FWHM = control_timelin[half2_index] - control_timelin[half1_index]
        #if ch == 0:
        #ch_new = [4, 1, 2, 3, 6, 5]
        ax2.plot(control_timeline, sum_waveform[board_idx][ch], '-', label='Channel '+str(ch))
        #plt.scatter(control_timeline[half1_index], sum_waveform[board_idx][ch][half1_index], color='r')
        #plt.scatter(control_timeline[half2_index], sum_waveform[board_idx][ch][half2_index], color='g')
        ax2.set_ylabel('signal, mV')
        ax2.set_xlabel('time, ns')
        ax2.set_title('Averaged from ' + str(number_events[board_idx]))
        ax2.legend()
        #ax2.set_ylim(-800, 100)
        ax2.set_xlim(-10, 130)

plt.savefig('270_5_11_20_averaged.png', dpi=600)
plt.show()