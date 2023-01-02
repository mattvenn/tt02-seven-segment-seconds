
# %%
import os
from subprocess import check_output
from bitarray import bitarray

def encode(g1, g2, K, in_bitarray):
    out_str = check_output(['./viterbi_main', '--reverse_polynomials', '--encode', f'{K}', f'{g1:d}', f'{g2:d}', in_bitarray.to01()], cwd=os.getcwd() + '/viterbi')
    #out_str = check_output(['./viterbi_main', '--encode', f'{K}', f'{g1:d}', f'{g2:d}', in_bitarray.to01()], cwd=os.getcwd() + '/viterbi')
    out_bitarray = bitarray(out_str.decode()[:-1])
    return out_bitarray

def encode_CCSDS(in_str):
    out_bitarray = encode(0b1111001, 0b1011011, 7, in_str)
    out_bitarray[1::2] = ~out_bitarray[1::2]
    return out_bitarray

def decode(g1, g2, K, in_bitarray):
    out_str = check_output(['./viterbi_main', f'{K}', f'{g1:d}', f'{g2:d}', in_bitarray.to01()], cwd=os.getcwd() + '/viterbi')
    out_bitarray = bitarray(out_str.decode()[:-1])
    return out_bitarray

def decode_CCSDS(in_bitarray):
    in_bitarray[1::2] = ~in_bitarray[1::2]
    return decode(0b1111001, 0b1011011, 7, in_bitarray)

def show_pad(in_bitarray, K):
    a = in_bitarray.to01()
    return a[:K-1] + '|' + a[K-1:]

def show_pad2(in_bitarray, K):
    a = in_bitarray.to01()
    return a[:-K] + '|' + a[-K:]

# %%
# CCSDS CC(7, 1/2)
in_bitarray = bitarray('100110')
#in_bitarray = bitarray('110010')

out_bitarray = encode_CCSDS(in_bitarray.copy())
print("Forward: " + show_pad(out_bitarray, 7))

in_bitarray = bitarray('011001')
#in_bitarray = bitarray('10101')

out_bitarray = encode_CCSDS(in_bitarray.copy())
print("Reverse: " + show_pad2(out_bitarray, 7))

# pass

# # %%
# #K = 3 variant: 
# #https://wokwi.com/projects/349523184124428883
# # %%%
# g1 = 0b111
# g2 = 0b101
# l = 3

# in_str = '0110'

# import os
# from subprocess import check_output
# a = check_output(['./viterbi_main', '--encode', f'{l}', f'{g1:d}', f'{g2:d}', in_str], cwd=os.getcwd() + '/viterbi')
# print(a)

# #a = '001101011100'
# a = a.decode()[:-1]

# b = encode(g1, g2, l, bitarray(in_str))
# c = decode(g1, g2, l, b.copy())

# d = encode_CCSDS(g1, g2, l, bitarray(in_str))
# e = decode_CCSDS(g1, g2, l, d.copy())

# pass


# c1 = a[0::2][:2] + '|' + a[0::2][2:]
# c2 = a[1::2][:2] + '|' + a[1::2][2:]

# print(g1)
# print(g2)
# print(c1)
# print(c2)

# # %%


# %%
