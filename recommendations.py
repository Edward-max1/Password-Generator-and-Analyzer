GENERAL_TIPS = [
    "Use a unique password for every account - never reuse passwords.",
    "Store passwords in a reputable password manager instead of memorising many.",
    "Turn on two-factor authentication (2FA) wherever it is offered.",
    "Never share passwords by email, SMS or chat, and never write them on sticky notes.",
    "Change a password immediately if you think an account has been exposed.",
]


def get_recommendations(result):
    advice = []

    if result["length"] < 8:
        advice.append("Your password is too short. Increase its length to at "
                      "least 12 characters.")
    elif result["length"] < 12:
        advice.append("Good start, but longer is stronger. Aim for 12 or more "
                      "characters.")

    if not result["has_upper"]:
        advice.append("Add uppercase letters (A-Z).")
    if not result["has_lower"]:
        advice.append("Include lowercase letters (a-z).")
    if not result["has_digit"]:
        advice.append("Add numbers (0-9).")
    if not result["has_special"]:
        advice.append("Include special characters such as ! @ # $ % ?")

    if result["sequence"] != "":
        advice.append("Avoid predictable sequences such as '" +
                      result["sequence"] + "'.")
    if result["repeated_run"] != "":
        advice.append("Avoid repeated characters such as '" +
                      result["repeated_run"] + "'.")
    if result["common_word"] != "":
        if result["common_is_exact"]:
            advice.append("This is one of the most commonly used passwords. "
                          "Choose something completely different.")
        else:
            advice.append("Avoid common passwords and words (like '" +
                          result["common_word"] + "'), even with symbols or "
                          "numbers swapped in.")

    if len(advice) == 0:
        advice.append("No obvious weaknesses were found. Keep it private and "
                      "use it for ONE account only.")
    return advice
