import generator
import analyzer
import recommendations

passed = 0
failed = 0


def check(description, condition):
    global passed, failed
    if condition:
        passed = passed + 1
    else:
        failed = failed + 1
        print("  FAILED:", description)


print("TEST 1: Analyzer on the required example passwords")
examples = [
    ("12345",         "Very Weak", 1, 5),
    ("password",      "Very Weak", 2, 4),
    ("Password123",   "Weak",      4, 2),
    ("Password@123",  "Weak",      6, 0),
    ("P@ssw0rd!2026", "Moderate",  6, 0),
    ("abcdefgh",      "Very Weak", 2, 4),
    ("AAAA1111!!!!",  "Weak",      5, 1),
]
print("  %-15s %5s  %-10s %s" % ("Password", "Score", "Label", "Met"))
for pw, label, met, missing_count in examples:
    r = analyzer.analyze_password(pw)
    print("  %-15s %5d  %-10s %d/6" % (pw, r["score"], r["label"], r["met_count"]))
    check(pw + " label", r["label"] == label)
    check(pw + " requirements met", r["met_count"] == met)
    check(pw + " missing count", len(r["missing"]) == missing_count)

print("TEST 2: Pattern detection")
check("sequence 123", analyzer.find_sequence("Pass123word") == "123")
check("sequence abc", analyzer.find_sequence("xxABCxx") == "ABC")
check("descending 987", analyzer.find_sequence("a987b") == "987")
check("no sequence", analyzer.find_sequence("Tq7#mZ") == "")
check("repeat run", analyzer.find_repeated_run("abXXXXcd") == "XXXX")
check("two repeats ok", analyzer.find_repeated_run("aabbcc") == "")
check("leet speak", analyzer.find_common("p@ssw0rd")[0] == "password")
check("hidden word", analyzer.find_common("MyDragonRocks")[0] == "dragon")
check("clean password", analyzer.find_common("Zx8#qLm2")[0] == "")

print("TEST 3: Analyzer edge cases (must not crash)")
r = analyzer.analyze_password("")
check("empty password", r["score"] == 0 and r["label"] == "Very Weak")
r = analyzer.analyze_password("   ")
check("spaces only", r["length"] == 3)
r = analyzer.analyze_password("pässwörd-密码-🔐")
check("unicode input", r["length"] > 0)
r = analyzer.analyze_password("Zx8#qLm2Vb4!Tn6@Rp9$")
check("long random password is Very Strong", r["label"] == "Very Strong")
r = analyzer.analyze_password("Zx8#qLm2")
check("8-char password capped at Moderate", r["score"] <= 64)

print("TEST 4: Recommendations change with the password")
rec_short = recommendations.get_recommendations(analyzer.analyze_password("abc"))
rec_good = recommendations.get_recommendations(
    analyzer.analyze_password("Zx8#qLm2Vb4!Tn6@Rp9$"))
check("short password gets length advice", "too short" in rec_short[0])
check("different passwords, different advice", rec_short != rec_good)
check("good password gets positive message", "No obvious weaknesses" in rec_good[0])
rec_a = recommendations.get_recommendations(analyzer.analyze_password("AAAA1111!!!!"))
check("repeat advice present", any("repeated" in x for x in rec_a))
check("missing lowercase advice present", any("lowercase" in x for x in rec_a))

print("TEST 5: Generator respects every combination of settings")
lengths = [4, 8, 12, 16, 32, 64]
combos = 0
for use_upper in [True, False]:
    for use_lower in [True, False]:
        for use_digits in [True, False]:
            for use_special in [True, False]:
                if not (use_upper or use_lower or use_digits or use_special):
                    continue
                for exclude in [True, False]:
                    for secure in [True, False]:
                        for length in lengths:
                            combos = combos + 1
                            for repeat in range(20):
                                pw, err = generator.generate_password(
                                    length, use_upper, use_lower, use_digits,
                                    use_special, exclude, secure)
                                ok = (err == "" and len(pw) == length)
                                if ok:
                                    has = [False, False, False, False]
                                    sets = [generator.UPPERCASE, generator.LOWERCASE,
                                            generator.DIGITS, generator.SPECIAL]
                                    for ch in pw:
                                        for k in range(4):
                                            if ch in sets[k]:
                                                has[k] = True
                                        if exclude and ch in "O0Il":
                                            ok = False
                                    wanted = [use_upper, use_lower, use_digits, use_special]
                                    if has != wanted:
                                        ok = False
                                if not ok:
                                    check("generator combo failed", False)
                                    break
print("  %d setting combinations x 20 passwords each checked" % combos)
check("all combinations were tested", combos == 15 * 2 * 2 * 6)

print("TEST 6: Generator validation")
pw, err = generator.generate_password(16, False, False, False, False)
check("no categories selected -> error", pw == "" and err != "")
pw, err = generator.generate_password(3, True, True, True, True)
check("length 3 -> error", pw == "" and err != "")
pw, err = generator.generate_password(65, True, True, True, True)
check("length 65 -> error", pw == "" and err != "")
pw, err = generator.generate_password(0, True, True, True, True)
check("length 0 -> error", pw == "" and err != "")
pw, err = generator.generate_password(-5, True, True, True, True)
check("negative length -> error", pw == "" and err != "")
pw, err = generator.generate_password(None, True, True, True, True)
check("None length -> error", pw == "" and err != "")
pw, err = generator.generate_password(4, True, True, True, True)
check("minimum length 4 with 4 categories works", err == "" and len(pw) == 4)

print("TEST 7: Generated passwords are different each time")
seen = []
for i in range(50):
    pw, err = generator.generate_password(16, True, True, True, True)
    seen.append(pw)
check("50 passwords are all different", len(seen) == 50 and
      all(seen.count(x) == 1 for x in seen))

print()
print("RESULT: %d checks passed, %d failed" % (passed, failed))
if failed == 0:
    print("ALL TESTS PASSED")
