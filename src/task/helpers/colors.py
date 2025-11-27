import random
import string


def hex_color_to_rgba_with_default_obscurity(value: str) -> str:
    value = value.lstrip('#')
    lv = len(value)
    rgb = tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))
    rgba = f'rgba{rgb}'[0:-1]
    rgba += ', 0.4)'
    return rgba


def rgba_color_with_default_obscurity_to_hex(value: str) -> str:
    rgb_elements = value.replace('rgba(', '')
    rgb_elements = rgb_elements.replace(', 0.4)', '')

    rgb_tuple = tuple(int(element) for element in rgb_elements.split(', '))
    return '#' + ''.join(f'{i:02X}' for i in rgb_tuple)


def generate_random_hex_color() -> str:
    color = '#'
    string.ascii_letters = 'ABCDEF'
    for i in range(6):
        next = random.choice(['num', 'char'])
        if next == 'char':
            color += random.choice(string.ascii_letters)
        else:
            color += str(random.randint(0, 9))

    return color

