
# Notes on binary/byte representations convention since its my number 1 source of confusion.
# These are not necessarily a general convention. It's just what I find most usefull to remember.

# When displaying a to be transmitted/processed bit sequence the bits are displayed last-transmitted-first:
# bitsequence: 10001111 10010011 11000100 01001000 10100100
#              ^ last bit tx'ed           first bit tx'ed ^
# index     n:                                ...9876543210
#
# My reason for this is that most DSP block-representations, i.e. FIR-filters, encoders, etc. show a 'right-shifting' representation
# where new bits enter on the left and are processed on the right.

# However, sometimes when displaying a received bit sequence the bits are displayed first-recieved-first:
# bitsequence: 00100101 00010010 00100011 11001001 11110001
#              ^ first bit received     last bit received ^
# index     n: 0123456789.....
# 
# My reason for this is that this way its easier to write down or type a received bit sequence (left-to-right).


# Same goes for a received byte sequence and transmitted byte sequence.
# Displaying a to-be-transmitted byte sequence:
# bytesequence: 0x8F 0x93 0xC3 0x48 0xA4
#               ^ last           first ^ 
# index      N:    4    3    2    1    0                     
# Displaying a received byte sequence:
# bytesequence: 0xA4 0x48 0xC3 0x93 0x8F
#               ^ first           last ^ 
# index      N:    0    1    2    3    4


# Note that the convention taken here is that the least-significant bit is transmitted first (LSb-first)
# This follows the transmission order for bits-of-a-byte
# of most serial transmission:
# https://erg.abdn.ac.uk/users/gorry/course/phy-pages/bit-order.html
# and Ethernet:
# https://en.wikipedia.org/wiki/Ethernet_frame#:~:text=Ethernet%20transmits%20data%20with%20the,is%20specified%20in%20IEEE%20802.3. 
# 
# For byte transmission the most-significant byte is transmitted first (MSB-first)

# Bit and Byte Endianess
# Things get more confusing when trying to tie these conventions to endiancy. S
# Some caution needs to be taken with Pythons default conversions/print-outs
# In python's bytearray I would use the 'received byte sequence' format to capture an array of bytes::
#
# a = bytearray(b'\xA4\x48\xC3\x93\x8F')
# print(hex(a[0]))
#
# Which prints '0xA4' thereby following our indexing where first received/transmitted byte is on index 0
# Although python follows the endianess of the processor, the basic conversions i.e. hex -> int follow a big-endian approach:
#
# a = int("0xA448C3938F", 0)
# print(a)
#
# Which prints 705595413391 which is the big-endian number of our byte sequence b'\xA4\x48\xC3\x93\x8F'.
# Additionally the easiest way to print a bit representation in python would be using f-strings:
#
# print(f'{0xA448C3938F:0>40b}')
# 
# Which prints: '10100100 01001000 11000011 10010011 10001111' (spaces added for clarity) which is the MSByte-first/MSbit-first representation 
# which does not represent the format described above following DSP/serial protocol logic

def number_of_ones_in_byte(n):
    
    if not hasattr(number_of_ones_in_byte, 'lut'):
        number_of_ones_in_byte.lut = [0] * 255
        for i in range(255):
            c = 0
            j = i
            while j:
                c += j%2
                j = j >> 1

            number_of_ones_in_byte.lut[i] = c

    return number_of_ones_in_byte.lut[n]

def access_bit_in_bytearray(input_bytearray, num):
    base = int(num // 8)
    shift = int(num % 8)
    return (input_bytearray[base] >> shift) & 0x1

def CCSDS_encode_bitarray(input_bitarray):

    output_bitarray = bytearray([0] * len(input_bitarray) * 2)

    state = 0x00
    next_byte = 0x00

    for n in range(len(input_bitarray)):
        in_bit = input_bitarray[n]
        C1, C2, next_state = CCSDS_encode(in_bit, state)
        print(f'{n:2d}: {state:06b}({state:2d}) → {next_state:06b}({next_state:2d}) in: {in_bit} C2C1: {C2}{C1} m: {int(C2 << 1 | C1)}')
        
        state = next_state
        output_bitarray[2*n] = C1
        output_bitarray[2*n + 1] = C2 ^ 0x1

    return output_bitarray

def CCSDS_encode_stream(input_bytearray):
    output_bytearray = bytearray()

    state = 0x00
    next_byte = 0x00

    for i in range(len(input_bytearray) * 8):
        in_bit = access_bit_in_bytearray(input_bytearray, i)
        C1, C2, next_state = CCSDS_encode(in_bit, state)
        print(f'{i:2d}: {state:06b}({state:2d}) → {next_state:06b}({next_state:2d})')
        # Collect bits onto a byte
        next_byte = ((C2 ^ 0x1) << 1 | C1) << 6 | (next_byte >> 2)
        
        # If the byte is full append it to the output array
        if (i % 4 == 3):
            output_bytearray.append(next_byte)
            next_byte = 0x00
        
        state = next_state

    return output_bytearray

def CCSDS_encode(in_bit, state):

    # Newest bit is on most-significant position of the 'input + state'-vector
    in_state = (in_bit << 6) | state

    G1 = 0b1111001
    G2 = 0b1011011
    
    C1 = number_of_ones_in_byte(in_state & G1) & 0x01
    C2 = number_of_ones_in_byte(in_state & G2) & 0x01

    # The next state after a clock cycle is provided
    next_state = in_state >> 1

    return C1, C2, next_state

import numpy as np

def viterbi(y, A, B, Pi=None):
    """
    Return the MAP estimate of state trajectory of Hidden Markov Model.

    Parameters
    ----------
    y : array (T,)
        Observation state sequence. int dtype.
    A : array (K, K)
        State transition matrix. See HiddenMarkovModel.state_transition  for
        details.
    B : array (K, M)
        Emission matrix. See HiddenMarkovModel.emission for details.
    Pi: optional, (K,)
        Initial state probabilities: Pi[i] is the probability x[0] == i. If
        None, uniform initial distribution is assumed (Pi[:] == 1/K).

    Returns
    -------
    x : array (T,)
        Maximum a posteriori probability estimate of hidden state trajectory,
        conditioned on observation sequence y under the model parameters A, B,
        Pi.
    T1: array (K, T)
        the probability of the most likely path so far
    T2: array (K, T)
        the x_j-1 of the most likely path so far
    """
    # From: https://stackoverflow.com/questions/9729968/python-implementation-of-viterbi-algorithm
    # Cardinality of the state space
    K = A.shape[0]
    # Initialize the priors with default (uniform dist) if not given by caller
    Pi = Pi if Pi is not None else np.full(K, 1 / K)
    T = len(y)
    T1 = np.empty((K, T), 'd')
    T2 = np.empty((K, T), 'B')

    # Initilaize the tracking tables from first observation
    T1[:, 0] = Pi * B[:, y[0]]
    T2[:, 0] = 0

    # Iterate throught the observations updating the tracking tables
    for i in range(1, T):
        T1[:, i] = np.max(T1[:, i - 1] * A.T * B[np.newaxis, :, y[i]].T, 1)
        T2[:, i] = np.argmax(T1[:, i - 1] * A.T, 1)

    # Build the output, optimal model trajectory
    x = np.empty(T, 'B')
    x[-1] = np.argmax(T1[:, T - 1])
    for i in reversed(range(1, T)):
        x[i - 1] = T2[x[i], i]

    return x, T1, T2

def pack(input_array, K = 8):
    # Packs an array of one-bit-per-byte to K-bits-per-byte

    # See: http://python-history.blogspot.com/2010/08/why-pythons-integer-division-floors.html
    output_length = -(len(input_array) // -K) 
    output_bytearray = bytearray([0] * output_length)

    for n in range(len(input_array)):
        base = int(n // K)
        shift = int(n % K)
        output_bytearray[base] = output_bytearray[base] | ((input_array[n] & 0x1) << shift)

    return output_bytearray

def unpack(input_array, K = 1):
    # Unpacks an array of bytes to K-bits-per-byte

    output_length = -((len(input_array) * 8) // -K)
    output_bytearray = bytearray([0] * output_length)

    for n in range(len(input_array) * 8):
        base = int(n // K)
        shift = int(n // K)
        output_bytearray[base] = output_bytearray[base] | access_bit_in_bytearray(input_array, n)

    return output_bytearray

def bitarray_as_bitstring(input_bitarray, reverse=False):
    string = ''.join([f'{input_bitarray[i]:d}' for i in range(len(input_bitarray))])
    return string[::-1] if reverse else string

def main():

    K = 7

    # Test encoding
    input_bitarray = [1, 0, 0, 1, 1, 0]
    input_bitarray = input_bitarray + [0] * (K-1)
    output_bitarray = CCSDS_encode_bitarray(input_bitarray)

    print("Input:")
    input_bitstring = bitarray_as_bitstring(input_bitarray, reverse=True)
    print(input_bitstring)

    print("Output:")
    output_bitstring = bitarray_as_bitstring(output_bitarray)
    print(output_bitstring[:K - 2] + '|' + output_bitstring[K - 2:])

    # Generates the Trellis table
    columns = ('I', 'S(n)', 'In', 'C1', 'C2', 'S(n+1)', 'm')
    trellis_table = np.empty((2**K, len(columns)), np.int8)
   
    for i, state in enumerate(range(2**(K - 1))):
        for in_bit in (0, 1):
            C1, C2, next_state = CCSDS_encode(in_bit, state)
            trellis_table[(2*i + in_bit), 0] = 2*i + in_bit
            trellis_table[(2*i + in_bit), 1] = state
            trellis_table[(2*i + in_bit), 2] = in_bit
            trellis_table[(2*i + in_bit), 3] = C1
            trellis_table[(2*i + in_bit), 4] = C2
            trellis_table[(2*i + in_bit), 5] = next_state
            trellis_table[(2*i + in_bit), 6] = (C2 << 1) | (C1 << 0)
        pass

    def trellis_table_to_tabluate(tt):
        cells = [['' for i in range(tt.shape[1])] for j in range(tt.shape[0])]
        for i in range(len(tt)):
            cells[i][0] = f'{tt[i, 0]}'
            cells[i][1] = f'{tt[i, 1]:06b}'
            cells[i][2] = f'{tt[i, 2]:d}'
            cells[i][3] = f'{tt[i, 3]:d}'
            cells[i][4] = f'{tt[i, 4]:d}'
            cells[i][5] = f'{tt[i, 5]:06b}'
            cells[i][6] = f'{tt[i, 6]:d}'
        return cells
    
    # from tabulate import tabulate
    # print(tabulate(trellis_table_to_tabluate(trellis_table), headers=columns, showindex="always"))

    # Construct the state transition matrix A
    A = np.zeros((2**(K - 1), 2**(K - 1))) 
    for state in range(2**(K - 1)):
        ii = np.argwhere(trellis_table[:,1] == state)
        number_of_possible_next_states = len(ii)
        probability = 1 / number_of_possible_next_states
        #print(number_of_possible_next_states)
        for i in ii.flatten():
            next_state = trellis_table[i,5]
            A[state, next_state] = probability
    
    # with np.printoptions(precision=1, suppress=True, threshold=np.inf):
    #     print(A)

    # Construct the emission matrix B 
    # Note the M=4 possible observations are encoded as dec( (C2 << 1) | C1 )
    # i.e. C1 = 0 C2 = 1 -> m = dec(0b10) = 2
    B = np.zeros((2**(K - 1), 4))
    for m in range(4):
        C1 = (m >> 0) & 0x1
        C2 = (m >> 1) & 0x1
        ii = np.argwhere((trellis_table[:,3] == C1) * (trellis_table[:,4] == C2))
        number_of_possible_states = len(ii)
        probability = 1 / number_of_possible_states
        for i in ii.flatten():
            state = trellis_table[i,1]
            B[state, m] = probability

    # with np.printoptions(suppress=True, threshold=np.inf):
    #     print(B)

    # Viterbi decoding:
    print("Input:")
    input_bitstring = bitarray_as_bitstring(input_bitarray, reverse=True)
    print(input_bitstring)

    print("Output (C1!C2):")
    output_bitstring = bitarray_as_bitstring(output_bitarray)
    print(output_bitstring)

    print("Output (C1C2):")
    output_bitarray_C1C2 = [output_bitarray[n] ^ 0x1 if n & 0x1 else output_bitarray[n] for n in range(len(output_bitarray))]
    output_bitstring_C1C2 = bitarray_as_bitstring(output_bitarray_C1C2)
    print(output_bitstring_C1C2)

    y = pack(output_bitarray_C1C2, 2)
    print("y_C2C1      = " + " ".join([f"{yy:02b}" for yy in y]))
    print("y_dec(C2C1) = " + " ".join([f"{yy:02d}" for yy in y]))

    #y = y[3:] # Throw away the first 3 symbols
    Pi = None
    Pi=np.zeros(len(A))
    Pi[0] = 1
    
    x, T1, T2 = viterbi(y, A, B, Pi)

    np.savetxt("T1.csv", T1, delimiter = ",")
    np.savetxt("T2.csv", T2, delimiter = ",")

    est_input_bitarray = bytearray([0] * int(len(output_bitarray) / 2))

    for i in range(len(x) - 1):
        state = x[i]
        next_state = x[i+1]

        ii = np.argwhere((trellis_table[:,1] == state) * (trellis_table[:,5] == next_state)).flatten()[0]
        in_bit = trellis_table[ii,2]
        C1 = trellis_table[ii,3]
        C2 = trellis_table[ii,4] 

        print(f'{i:2d}: {state:06b}({state:2d}) → {next_state:06b}({next_state:2d}) in: {in_bit} C2C1: {C2}{C1} m: {int(C2 << 1 | C1)}')

        est_input_bitarray[i] = in_bit

    print("Estimate of original sequence:")
    print(bitarray_as_bitstring(est_input_bitarray))
    pass

# Something goes wrong here at the 3rd transition from 100000(32) -> 
# For that the Trellis table has the following entries:
#       I    S(n)    In    C1    C2    S(n+1)
# 64   64  100000     0     1     0    010000
# 65   65  100000     1     0     1    110000
# The viterbi picks 010000(16) whereas it should have picked 110000(48)
# Should perhaps the in_bit be included as the 'hidden state'

if __name__ == "__main__":
    main()