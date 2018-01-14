from SimulaQron.cqc.pythonLib.cqc import *
import png


# Wait for n qubits to be received
def wait_for_n_qubits(n, Receiver, print_info=False):
    qubits = []
    while len(qubits) < n:
        qubits.append(Receiver.recvQubit(print_info=print_info))

    return qubits


# Wait for n EPR pairs to be received
def wait_for_n_epr_pairs(n, Receiver, print_info=False):
    epr_pairs = []
    while len(epr_pairs) < n:
        epr_pairs.append(Receiver.recvEPR(print_info=print_info))

    return epr_pairs


# For arrays qubits and epr_pairs, measure qubits using super dense coding protocol
def decode_message(qubits, epr_pairs):
    i = 0
    message = ''
    while i < len(qubits):
        qubits[i].cnot(epr_pairs[i])
        qubits[i].H()
        message += str(qubits[i].measure())
        message += str(epr_pairs[i].measure())
        i += 1

    return message


# Protocol for receiving images given an array of expected incoming quantum data
def receive_image(incoming_data_stream, Receiver):
    image_data = []
    i = 0
    while i < len(incoming_data_stream):
        num_incoming_qubits = incoming_data_stream[i]
        epr_pairs = wait_for_n_epr_pairs(num_incoming_qubits, Receiver)
        qubits = wait_for_n_qubits(num_incoming_qubits, Receiver)
        image_data.append(decode_message(qubits, epr_pairs))
        i += 1

    return image_data


def decompress(image_data):
    pixel_data = []
    for pixel in image_data:
        if pixel == '00':
            pixel_data += ['0', '0', '0', '11111111']
        elif pixel == '01':
            pixel_data += ['11111111', '0', '0', '11111111']
        elif pixel == '10':
            pixel_data += ['0', '11111111', '0', '11111111']
        else:
            pixel_data += ['11111111', '11111111', '11111111', '11111111']

    return pixel_data


def decode_png(image_data, is_restrictive_case=False):
    width = int(image_data[0], 2)
    height = int(image_data[1], 2)

    if is_restrictive_case:
        pixel_data = decompress(image_data[2:])
    else:
        pixel_data = image_data[2:]

    # Reconstruct the image data formatted for PyPNG library
    rows = []
    cur_row = 0
    while cur_row < height:
        row = []
        cur_col = 0
        offset = cur_row * width * 4
        while cur_col < width * 4:
            row.append(int(pixel_data[cur_col + offset], 2))
            cur_col += 1
        rows.append(row)
        cur_row += 1

    return width, height, rows


#
# main
#
def main():
    # Flag used to restrict to 2x2 PNG images composed of red, green, black,
    # and white colours
    is_restrictive_case = True

    # Flag if image should be written or printed
    write_image = True

    # Initialize the connection
    Bob = CQCConnection("Bob")
    Bob.startClassicalServer()

    # Receive data about incoming quantum data
    incoming_data_stream = list(Bob.recvClassical())

    image_data = receive_image(incoming_data_stream, Bob)
    Bob.close()

    # Prepend the 2x2 dimensions for decoding
    if is_restrictive_case:
        image_data = ['10', '10'] + image_data

    decoded_image_data = decode_png(image_data, is_restrictive_case)
    if write_image:
        writer = png.Writer(decoded_image_data[0], decoded_image_data[1], alpha=True)
        out = open('received_image.png', 'wb')
        writer.write(out, decoded_image_data[2])
        print('------ IMAGE RECEIVED SUCCESSFULLY ------')
    else:
        print(decoded_image_data)


##################################################################################################
main()
