import random
import secrets

UPPERCASE = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
LOWERCASE = "abcdefghijklmnopqrstuvwxyz"
DIGITS = "0123456789"
SPECIAL = "!@#$%^&*()-_=+?"
CONFUSING = "O0Il"

MIN_LENGTH = 4
MAX_LENGTH = 64
DEFAULT_LENGTH = 16


def remove_confusing(characters):
    cleaned = ""
    for ch in characters:
        if ch not in CONFUSING:
            cleaned = cleaned + ch
    return cleaned


def get_selected_pools(use_upper, use_lower, use_digits, use_special,
                       exclude_confusing):
    pools = []
    if use_upper:
        pools.append(UPPERCASE)
    if use_lower:
        pools.append(LOWERCASE)
    if use_digits:
        pools.append(DIGITS)
    if use_special:
        pools.append(SPECIAL)

    if exclude_confusing:
        cleaned_pools = []
        for pool in pools:
            cleaned_pools.append(remove_confusing(pool))
        pools = cleaned_pools
    return pools


def validate_settings(length, use_upper, use_lower, use_digits, use_special):
    if length is None:
        return "Please enter a valid whole number for the password length."
    if length < MIN_LENGTH or length > MAX_LENGTH:
        return ("Password length must be between " + str(MIN_LENGTH) +
                " and " + str(MAX_LENGTH) + " characters.")

    selected = 0
    for choice in [use_upper, use_lower, use_digits, use_special]:
        if choice:
            selected = selected + 1

    if selected == 0:
        return "Select at least one character type (A-Z, a-z, 0-9 or symbols)."
    if length < selected:
        return "The length is too short to include every selected character type."
    return ""


def random_below(n, secure_mode):
    if secure_mode:
        return secrets.randbelow(n)
    return random.randint(0, n - 1)


def pick_character(characters, secure_mode):
    position = random_below(len(characters), secure_mode)
    return characters[position]


def shuffle_characters(items, secure_mode):
    for i in range(len(items) - 1, 0, -1):
        j = random_below(i + 1, secure_mode)
        temp = items[i]
        items[i] = items[j]
        items[j] = temp
    return items


def check_against_settings(password, length, use_upper, use_lower,
                           use_digits, use_special, exclude_confusing):
    if len(password) != length:
        return "Generated password has the wrong length."

    categories = [
        (UPPERCASE, use_upper),
        (LOWERCASE, use_lower),
        (DIGITS, use_digits),
        (SPECIAL, use_special),
    ]
    for full_set, selected in categories:
        found = False
        for ch in password:
            if ch in full_set:
                found = True
        if selected and not found:
            return "Generated password is missing a selected character type."
        if not selected and found:
            return "Generated password contains an unselected character type."

    if exclude_confusing:
        for ch in password:
            if ch in CONFUSING:
                return "Generated password contains a confusing character."
    return ""


def generate_password(length, use_upper, use_lower, use_digits, use_special,
                      exclude_confusing=False, secure_mode=False):
    error = validate_settings(length, use_upper, use_lower,
                              use_digits, use_special)
    if error != "":
        return "", error

    pools = get_selected_pools(use_upper, use_lower, use_digits,
                               use_special, exclude_confusing)
    all_characters = "".join(pools)

    chars = []
    for pool in pools:
        chars.append(pick_character(pool, secure_mode))

    while len(chars) < length:
        chars.append(pick_character(all_characters, secure_mode))

    chars = shuffle_characters(chars, secure_mode)
    password = "".join(chars)

    problem = check_against_settings(password, length, use_upper, use_lower,
                                     use_digits, use_special, exclude_confusing)
    if problem != "":
        return "", problem
    return password, ""
