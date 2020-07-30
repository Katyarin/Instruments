import pyvisa
import matplotlib.pyplot as plt
import struct

class GEN_numbers:
    my_instrument = None

    def __init__(self, ip_addr):
        rm = pyvisa.ResourceManager()
        self.my_instrument = rm.open_resource('TCPIP0::%s::INSTR' % ip_addr)
        print(self.my_instrument.query('*IDN?'))

    def signal(self, frequency, amplitude, offset='def', function='PULS'):
        '''Amplitude и offset в вольтах. Def = 1 Vpp и 0 V соответственно.
        Частота должна задаваться строкой с Гц, КГц, или МГц.
        Возможные функции: DC, NOIS, SIN, PULS, RAMP, SQU, USER'''
        self.my_instrument.write(':APPL: ' + function + ' ' +
                                 str(frequency) + ' ,' + str(amplitude) + ' ,' + str(offset))