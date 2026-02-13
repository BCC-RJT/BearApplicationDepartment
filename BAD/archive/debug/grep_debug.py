
matches = []
with open("src/bridge/tickets_assistant.py", "r", encoding="utf-8") as f:
    for i, line in enumerate(f):
        if "close" in line.lower():
            matches.append((i+1, line.strip()))

if matches:
    print(f"Found {len(matches)} matches:")
    for m in matches:
        # print only first 10 matches to avoid spam
        if m[0] < 1000: # print all
            print(f"Line {m[0]}: {m[1]}")
else:
    print("No matches for 'close'")
