'''TODO:
функция, которая устанавливает шкалу и оффсет
по данному пользователем минимумум и максимуму его сигнала '''
import pyvisa
import struct


class Osc:
    my_instrument = None
    alive = False
    want_osc = 'AGILENT TECHNOLOGIES,DSO7054B,MY50340381,06.16.0001\n'

    def __init__(self, ip_addr):
        print('Initialising...')
        rm = pyvisa.ResourceManager()
        self.my_instrument = rm.open_resource('TCPIP0::%s::INSTR' % ip_addr)
        IDN_os = self.my_instrument.query('*IDN?')
        print('Oscilloscope name: ', IDN_os)
        if self.want_osc == IDN_os:
            self.alive = True
        print('Alive: ', self.alive)

    def get_data(self, n_channell):
        self.my_instrument.write(':WAVeform:SOURce CHANnel' + str(n_channell)) #set the reading channel
        self.my_instrument.write(':WAVeform:FORMat BYTE')
        raw_data = self.my_instrument.query_binary_values(':WAVeform:DATA?')
        raw_preamble = self.my_instrument.query(':WAVeform:PREamble?')
        bytes_data = []
        for entry in raw_data:
            bytes_data.extend(bytearray(struct.pack("f", entry)))
        k = 0
        preamble = [[]]
        p = 0
        for i in range(len(raw_preamble)):
            if raw_preamble[i] == ',' or i == len(raw_preamble) - 1:
                preamble[k] = float(raw_preamble[p:i])
                p = i + 1
                k += 1
                preamble.append([])
        preamble.pop()
        data = [(i - preamble[9]) * preamble[7] + preamble[8] for i in bytes_data]
        time = [(i - preamble[6]) * preamble[4] + preamble[5] for i in range(len(bytes_data))]
        return time, data

    def set_data_scale(self, n_channell, scale, V_or_mV='mV'):
        '''В переменную V_or_mV нужно написать строку V или mV'''
        self.my_instrument.write(':CHANnel' + str(n_channell)+ ':SCALe ' + str(scale) + V_or_mV)

    def trigger_set(self, n_channell, scale, slope='NEGative'):
        """<slope> ::= {NEGative | POSitive | EITHer | ALTernate}
        scale in V"""
        self.my_instrument.write(':TRIGger:EDGE:SOURce CHANnel' + str(n_channell))
        self.my_instrument.write(':TRIGger:EDGE:SLOPe ' + slope)
        self.my_instrument.write(':TRIGger:EDGE:LEVel ' + str(scale) + ', CHANnel' + str(n_channell))

    def set_offset(self, n_channel, scale, V_or_mV='mV'):
        self.my_instrument.write(':CHANnel' + str(n_channel) + ':OFFSet ' + str(scale) + V_or_mV)

    def signal_in_window(self, n_channell, s_min, s_max):
        window_size = s_max - s_min
        self.set_data_scale()
