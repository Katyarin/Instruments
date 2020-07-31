import chatter
import time


class CAEN_data:

    shotn = None

    def __init__(self):
        shot_filename = "shotn.txt"
        isPlasma = False
        with open(shot_filename, 'r') as shotn_file:
            line = shotn_file.readline()
            self.shotn = int(line)


    def increment_shotn(self):
        with open(shot_filename, 'w') as shotn_file:
            shotn_file.seek(0)
            self.shotn += 1
            shotn_file.write('%d' % shotn)

        print(self.shotn)

    def connect_and_arm(self):
        chatter.connect()

        chatter.send_cmd(chatter.Commands.Alive)
        print(chatter.read())

        time.sleep(0.1)

        self.increment_shotn()
        chatter.send_cmd(chatter.Commands.Arm, [shotn, isPlasma])
        print(chatter.read())
        print('CAEN ready for data...')

    #time.sleep(10)

    def get_data_and_disarm(self):
        chatter.send_cmd(chatter.Commands.Disarm)
        print(chatter.read())

        chatter.send_cmd(chatter.Commands.Close)
        time.sleep(0.5)
        chatter.disconnect()

        print('Normal CAEN exit')
