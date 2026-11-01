import json
import sys


def to_minutes(clock):
    hours, mins = clock.split(":")
    return int(hours) * 60 + int(mins)


def to_clock(total):
    return f"{total // 60:02d}:{total % 60:02d}"


def free_slots(day, meetings, shortest):
    start, end = to_minutes(day["start"]), to_minutes(day["end"])
    busy = sorted(
        (max(start, to_minutes(m["start"])), min(end, to_minutes(m["end"])))
        for m in meetings
        if m["date"] == day["date"]
    )
    slots, cursor = [], start
    for busy_start, busy_end in busy:
        if busy_start > cursor:
            slots.append([cursor, busy_start])
        cursor = max(cursor, busy_end)
    if cursor < end:
        slots.append([cursor, end])
    return [[day["date"], a, b] for a, b in slots if b - a >= shortest]


def place_extras(slots, extras, blocks, unplanned):
    for extra in extras:
        left = round(extra["hours"] * 60)
        for slot in slots:
            if left == 0:
                break
            take = min(left, slot[2] - slot[1])
            if take <= 0:
                continue
            blocks.append({"date": slot[0], "start": to_clock(slot[1]), "end": to_clock(slot[1] + take), "kind": "extra", "title": extra["title"]})
            slot[1] += take
            left -= take
        if left:
            unplanned.append({"kind": "extra", "title": extra["title"], "hoursLeft": round(left / 60, 2)})


def place_tickets(slots, tickets, limit, focus, blocks, unplanned):
    queue = [{**t, "order": i, "left": round(t["hours"] * 60), "given": 0} for i, t in enumerate(tickets)]
    active = []
    for date, start, end in slots:
        cursor = start
        while cursor < end:
            while len(active) < limit and queue:
                active.append(queue.pop(0))
            if not active:
                return
            current = min(active, key=lambda t: (t["given"], t["order"]))
            take = min(current["left"], end - cursor, focus)
            blocks.append({"date": date, "start": to_clock(cursor), "end": to_clock(cursor + take), "kind": "ticket", "key": current["key"], "title": current["title"]})
            current["left"] -= take
            current["given"] += take
            cursor += take
            if current["left"] == 0:
                active.remove(current)
    for t in sorted(active + queue, key=lambda t: t["order"]):
        unplanned.append({"kind": "ticket", "key": t["key"], "title": t["title"], "hoursLeft": round(t["left"] / 60, 2)})


def plan(data):
    shortest = data.get("minSlotMinutes", 30)
    meetings = data.get("meetings", [])
    order = [day["date"] for day in data["days"]]
    slots = [slot for day in data["days"] for slot in free_slots(day, meetings, shortest)]
    blocks, unplanned = [], []
    place_extras(slots, data.get("extras", []), blocks, unplanned)
    slots = [slot for slot in slots if slot[2] - slot[1] >= shortest]
    place_tickets(slots, data.get("tickets", []), data.get("maxTickets", 2), data.get("focusMinutes", 120), blocks, unplanned)
    blocks.sort(key=lambda b: (order.index(b["date"]), b["start"]))
    return {"blocks": blocks, "unplanned": unplanned}


if __name__ == "__main__":
    with open(sys.argv[1]) as handle:
        print(json.dumps(plan(json.load(handle)), indent=2))
