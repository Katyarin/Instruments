import os
import ijson
import itertools

path = 'c:/work/Data/Polychromators/2020.11.05/'
HEADER_FILE = 'header'
FILE_EXT = 'json'
board_file = None


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
    for board_id in range(4):
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


#timestamps = get_shot('00274')  # This reads all files to count total events.
#for board in range(4):
#    print('Board %d recordered %d events.' % (board, len(timestamps[board])))

counter = 0
for event in get_event('00274', 0):
    if counter < 2:
        print(counter, event['groups'][0].keys())
    counter += 1

board_file.close()
