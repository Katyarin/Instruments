import pyvisa
import matplotlib.pyplot as plt
import struct


my_instrument = None
ip_addr = "192.168.10.104" # should match the instrument‘s IP address
visa_address = 'TCPIP0::%s::INSTR' % ip_addr

rm = pyvisa.ResourceManager()
rm.list_resources()
#('ASRL1::INSTR', 'ASRL2::INSTR', 'GPIB0::14::INSTR')
my_instrument = rm.open_resource(visa_address)
print(my_instrument.query('*IDN?'))
print(my_instrument.query(':ACQuire:COMPlete?'))
print(my_instrument.write(':TRIGger:EDGE:LEVel 0.5, CHANnel1 '))
print(my_instrument.write(':WAVeform:SOURce CHANnel1'))
print(my_instrument.write(':WAVeform:FORMat BYTE'))
print(my_instrument.query(':WAVeform:POINts?'))
raw_data = my_instrument.query_binary_values(':WAVeform:DATA?')
#print(my_instrument.query(':WAVeform:DATA?'))
print("we are here")
raw_preamble = my_instrument.query(':WAVeform:PREamble?')
print(len(raw_data))

bytes_data = []
for entry in raw_data:
    bytes_data.extend(bytearray(struct.pack("f", entry)))



k = 0
preamble = [[]]
p = 0
for i in range(len(raw_preamble)):
    if raw_preamble[i] == ',' or  i == len(raw_preamble) - 1:
        preamble[k] = float(raw_preamble[p:i])
        p = i + 1
        k += 1
        preamble.append([])
preamble.pop()
print(preamble)

data = []
for i in bytes_data:
    data.append((i - preamble[9]) * preamble[7] + preamble[8])
print(data)
time = [((i - preamble[6]) * preamble[4] + preamble[5]) * 1000 for i in range(len(bytes_data))]
plt.plot(time, data)
plt.show()
