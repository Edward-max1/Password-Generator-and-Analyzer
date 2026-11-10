COMMON_PASSWORDS = [
    "123456", "12345678", "123456789", "12345", "1234567", "1234567890",
    "password", "password1", "passw0rd", "qwerty", "qwerty123", "abc123",
    "abcdefgh", "abcd1234", "111111", "000000", "123123", "12341234",
    "admin", "letmein", "welcome", "iloveyou", "monkey", "dragon",
    "football", "baseball", "sunshine", "princess", "login", "master",
    "trustno1", "1q2w3e4r", "qazwsx", "asdfghjkl",
]

COMMON_WORDS = [
    "password", "qwerty", "admin", "welcome", "letmein", "iloveyou",
    "monkey", "dragon", "football", "baseball", "sunshine", "princess",
    "login", "master", "trustno1", "123456", "asdfg", "abc123",
]

LEET_MAP = {"@": "a", "4": "a", "0": "o", "3": "e", "$": "s",
            "5": "s", "1": "i", "!": "i", "7": "t"}

TOTAL_REQUIREMENTS = 6


def unleet(text):
    result = ""
    for ch in text:
        if ch in LEET_MAP:
            result = result + LEET_MAP[ch]
        else:
            result = result + ch
    return result


def find_repeated_run(password, min_run=3):
    start = 0
    for i in range(1, len(password) + 1):
        if i == len(password) or password[i] != password[start]:
            if i - start >= min_run:
                return password[start:i]
            start = i
    return ""


def find_sequence(password, min_run=3):
    text = password.lower()
    for i in range(len(text) - 2):
        a, b, c = text[i], text[i + 1], text[i + 2]
        if not (a.isalnum() and b.isalnum() and c.isalnum()):
            continue
        step = ord(b) - ord(a)
        if (step == 1 or step == -1) and ord(c) - ord(b) == step:
            end = i + 3
            while (end < len(text) and text[end].isalnum()
                   and ord(text[end]) - ord(text[end - 1]) == step):
                end = end + 1
            return password[i:end]
    return ""


def find_common(password):
    lowered = password.lower()
    disguised = unleet(lowered)

    if lowered in COMMON_PASSWORDS:
        return lowered, True
    if disguised in COMMON_PASSWORDS:
        return disguised, True

    for word in COMMON_WORDS:
        if word in lowered or word in disguised:
            return word, False
    return "", False


def classify_score(score):
    if score < 25:
        return "Very Weak"
    elif score < 45:
        return "Weak"
    elif score < 65:
        return "Moderate"
    elif score < 85:
        return "Strong"
    else:
        return "Very Strong"


def analyze_password(password):
    length = len(password)

    has_upper = False
    has_lower = False
    has_digit = False
    has_special = False
    for ch in password:
        if ch.isupper():
            has_upper = True
        elif ch.islower():
            has_lower = True
        elif ch.isdigit():
            has_digit = True
        else:
            has_special = True

    requirements = [
        ("At least 8 characters", length >= 8),
        ("At least 12 characters (recommended)", length >= 12),
        ("At least one uppercase letter (A-Z)", has_upper),
        ("At least one lowercase letter (a-z)", has_lower),
        ("At least one digit (0-9)", has_digit),
        ("At least one special character (!@#$...)", has_special),
    ]
    met_count = 0
    missing = []
    for description, met in requirements:
        if met:
            met_count = met_count + 1
        else:
            missing.append(description)

    repeated_run = find_repeated_run(password)
    sequence = find_sequence(password)
    common_word, is_exact = find_common(password)

    if length < 20:
        length_points = length * 2
    else:
        length_points = 40

    categories_used = 0
    for flag in [has_upper, has_lower, has_digit, has_special]:
        if flag:
            categories_used = categories_used + 1
    variety_points = categories_used * 10

    different = ""
    for ch in password:
        if ch not in different:
            different = different + ch
    if length > 0:
        uniqueness_points = int(20 * len(different) / length)
    else:
        uniqueness_points = 0

    score = length_points + variety_points + uniqueness_points

    if repeated_run != "":
        score = score - 15
    if sequence != "":
        score = score - 15
    if common_word != "":
        if is_exact:
            score = min(score, 5)
        else:
            score = score - 25

    if length < 8:
        score = min(score, 39)
    elif length < 12:
        score = min(score, 64)

    if score < 0:
        score = 0
    if score > 100:
        score = 100

    return {
        "length": length,
        "has_upper": has_upper,
        "has_lower": has_lower,
        "has_digit": has_digit,
        "has_special": has_special,
        "requirements": requirements,
        "met_count": met_count,
        "total_requirements": TOTAL_REQUIREMENTS,
        "missing": missing,
        "repeated_run": repeated_run,
        "sequence": sequence,
        "common_word": common_word,
        "common_is_exact": is_exact,
        "score": score,
        "label": classify_score(score),
    }
