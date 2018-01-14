from SimulaQron.cqc.pythonLib.cqc import *
import png


def prepare_state(state, q):
    if state == "00":
        q.I()
    elif state == "01":
        q.X()
    elif state == "10":
        q.Z()
    elif state == "11":
        q.Y()


def send_binary_message(message, Sender, Receiver):
    pairs_needed = int(len(message) / 2)
    epr_pairs = []

    for i in range(pairs_needed):
        epr_pairs.append(Sender.createEPR(Receiver, print_info=False))

    i = 0
    n = 0
    while i < len(message):
        prepare_state(message[i:i + 2], epr_pairs[n])
        i += 2
        n += 1

    for q in epr_pairs:
        Sender.sendQubit(q, Receiver, print_info=False)


def to_even_len_binary(f):
    t = str(bin(f))[2:]
    if len(t) % 2 != 0:
        t = '0' + t
    return t


def encode_png_for_sending(path_to_image, is_restrictive_case=False):
    reader = png.Reader(path_to_image)
    file_info = reader.read_flat()
    compressed = [to_even_len_binary(file_info[0]), to_even_len_binary(file_info[1])]
    pixel_data = []

    for pixel in list(file_info[2]):
        pixel_data.append(to_even_len_binary(pixel))

    if is_restrictive_case:
        i = 0
        while i < len(pixel_data):
            compressed.append(compress(pixel_data[i], pixel_data[i + 1], pixel_data[i + 2]))
            i += 4
        return compressed
    else:
        return compressed + pixel_data


def compress(p1, p2, p3):
    # red
    if p1 == '11111111' and p2 == '00' and p3 == '00':
        return '01'
    # green
    elif p2 == '11111111' and p1 == '00' and p3 == '00':
        return '10'
    # white
    elif p1 == '11111111' and p2 == '11111111' and p3 == '11111111':
        return '11'
    # black
    else:
        return '00'


#
# main
#
def main():
    # Flag used to restrict to 2x2 PNG images composed of red, green, black,
    # and white colours
    is_restrictive_case = True

    # Initialize the connection
    Alice = CQCConnection("Alice")
    image_data = encode_png_for_sending('sample_photo.png', is_restrictive_case)
    bits_to_receive = []

    for d in image_data:
        bits_to_receive.append(int(len(d) / 2))

    if is_restrictive_case:
        image_data = image_data[2:]
        bits_to_receive = bits_to_receive[2:]

    Alice.sendClassical('Bob', bits_to_receive)
    for d in image_data:
        send_binary_message(d, Alice, 'Bob')

    # Stop the connections
    Alice.close()


##################################################################################################
main()
