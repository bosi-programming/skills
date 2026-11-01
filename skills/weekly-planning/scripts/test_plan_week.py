import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from plan_week import plan

SCRIPT = Path(__file__).resolve().parent / "plan_week.py"


def minutes(clock):
    hours, mins = clock.split(":")
    return int(hours) * 60 + int(mins)


def day(date, start="09:00", end="18:00"):
    return {"date": date, "start": start, "end": end}


def ticket(key, hours):
    return {"key": key, "title": f"Work on {key}", "hours": hours}


def week(**overrides):
    data = {
        "maxTickets": 2,
        "days": [day("2026-11-02"), day("2026-11-03"), day("2026-11-04")],
        "meetings": [],
        "tickets": [],
        "extras": [],
    }
    data.update(overrides)
    return data


def absolute(block, dates):
    return dates.index(block["date"]) * 24 * 60 + minutes(block["start"]), dates.index(block["date"]) * 24 * 60 + minutes(block["end"])


def overlaps(a, b):
    return a[0] < b[1] and b[0] < a[1]


def most_in_progress(data, result):
    dates = [d["date"] for d in data["days"]]
    unfinished = {item.get("key") for item in result["unplanned"]}
    spans = {}
    for block in result["blocks"]:
        if block["kind"] != "ticket":
            continue
        start, end = absolute(block, dates)
        first, last = spans.get(block["key"], (start, end))
        spans[block["key"]] = (min(first, start), max(last, end))
    spans = {key: (first, float("inf") if key in unfinished else last) for key, (first, last) in spans.items()}
    return max(sum(1 for first, last in spans.values() if first <= moment < last) for moment, _ in spans.values())


class PlanWeekTest(unittest.TestCase):
    def test_no_block_overlaps_a_meeting(self):
        meetings = [
            {"date": "2026-11-02", "start": "10:00", "end": "11:00", "title": "Standup"},
            {"date": "2026-11-03", "start": "13:30", "end": "15:00", "title": "Planning"},
        ]
        data = week(meetings=meetings, tickets=[ticket("ABC-1", 12), ticket("ABC-2", 8)], extras=[{"title": "Expenses", "hours": 1}])
        result = plan(data)
        dates = [d["date"] for d in data["days"]]
        for block in result["blocks"]:
            for meeting in meetings:
                self.assertFalse(overlaps(absolute(block, dates), absolute(meeting, dates)), block)

    def test_never_more_than_max_tickets_in_progress(self):
        for limit in (1, 2, 3):
            data = week(maxTickets=limit, tickets=[ticket("ABC-1", 5), ticket("ABC-2", 7), ticket("ABC-3", 4), ticket("ABC-4", 6)])
            self.assertEqual(most_in_progress(data, plan(data)), limit)

    def test_blocks_are_at_most_two_hours(self):
        result = plan(week(tickets=[ticket("ABC-1", 9)]))
        self.assertTrue(all(minutes(b["end"]) - minutes(b["start"]) <= 120 for b in result["blocks"]))

    def test_two_tickets_run_side_by_side(self):
        result = plan(week(tickets=[ticket("ABC-1", 6), ticket("ABC-2", 6)]))
        first_day = {block["key"] for block in result["blocks"] if block["date"] == "2026-11-02"}
        self.assertEqual(first_day, {"ABC-1", "ABC-2"})

    def test_ticket_that_does_not_fit_goes_to_unplanned(self):
        result = plan(week(days=[day("2026-11-02")], tickets=[ticket("ABC-1", 6), ticket("ABC-2", 6)]))
        unplanned = {item["key"]: item["hoursLeft"] for item in result["unplanned"]}
        planned = sum(minutes(b["end"]) - minutes(b["start"]) for b in result["blocks"]) / 60
        self.assertEqual(planned, 9)
        self.assertEqual(sum(unplanned.values()), 3)

    def test_day_left_out_gets_no_block(self):
        data = week(days=[day("2026-11-02"), day("2026-11-03"), day("2026-11-05")], tickets=[ticket("ABC-1", 40)])
        result = plan(data)
        self.assertNotIn("2026-11-04", {block["date"] for block in result["blocks"]})

    def test_gap_shorter_than_thirty_minutes_is_dropped(self):
        meetings = [
            {"date": "2026-11-02", "start": "09:20", "end": "12:00", "title": "Workshop"},
            {"date": "2026-11-02", "start": "12:15", "end": "17:40", "title": "Offsite"},
        ]
        result = plan(week(days=[day("2026-11-02")], meetings=meetings, tickets=[ticket("ABC-1", 8)]))
        self.assertEqual(result["blocks"], [])

    def test_extras_avoid_meetings_and_do_not_take_a_ticket_slot(self):
        meetings = [{"date": "2026-11-02", "start": "09:00", "end": "10:00", "title": "Standup"}]
        data = week(days=[day("2026-11-02")], meetings=meetings, maxTickets=1, tickets=[ticket("ABC-1", 2)], extras=[{"title": "Expenses", "hours": 1}])
        result = plan(data)
        extras = [block for block in result["blocks"] if block["kind"] == "extra"]
        self.assertEqual([(b["start"], b["end"]) for b in extras], [("10:00", "11:00")])
        self.assertEqual(sum(minutes(b["end"]) - minutes(b["start"]) for b in result["blocks"] if b["kind"] == "ticket"), 120)

    def test_cli_reads_a_file_and_prints_json(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
            json.dump(week(tickets=[ticket("ABC-1", 2)]), handle)
        output = subprocess.run([sys.executable, str(SCRIPT), handle.name], capture_output=True, text=True, check=True).stdout
        self.assertEqual(json.loads(output)["blocks"][0], {"date": "2026-11-02", "start": "09:00", "end": "11:00", "kind": "ticket", "key": "ABC-1", "title": "Work on ABC-1"})


if __name__ == "__main__":
    unittest.main()
