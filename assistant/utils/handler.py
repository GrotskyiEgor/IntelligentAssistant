from rapidfuzz import process, utils

commands_list = {
    "open": ["открой", "відкрий", "запусти"],
    "close": ["закрой", "закрий", "зупини", "останови"]
}

def define_command(input):
    text = utils.default_process(input).split()

    min_score = 70
    min_margin = 15
    commands = []

    for i, word in enumerate(text):
        matches = []

        for command, keywords in commands_list.items():
            result = process.extract(word, keywords, limit=1)

            if result:
                best_word, best_score, _ = result[0]
                matches.append((command, best_word, best_score))

        if not matches:
            continue

        matches.sort(key=lambda x: x[2], reverse=True)

        command, best_word, best_score = matches[0]

        if len(matches) > 1:
            margin = best_score - matches[1][2]

            if best_score < min_score or margin < min_margin:
                continue
        elif best_score < min_score:
            continue

        if command not in [x[0] for x in commands]:
            commands.append((command, i))

    return commands