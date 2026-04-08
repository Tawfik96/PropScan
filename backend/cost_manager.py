import json
import os
from datetime import datetime

COST_FILE = "costs.json"


def load_cost_state():
    if not os.path.exists(COST_FILE):
        return {
            "date": datetime.now().date().isoformat(),
            "daily_cost": 0.0,
            "max_daily_limit": 2.0
        }

    with open(COST_FILE, "r") as f:
        return json.load(f)


def save_cost_state(state):
    with open(COST_FILE, "w") as f:
        json.dump(state, f, indent=2)


def check_and_update_cost(new_cost: float, raise_on_limit=False):
    state = load_cost_state()

    today = datetime.now().date().isoformat()

    # reset daily cost if new day
    if state["date"] != today:
        state["date"] = today
        state["daily_cost"] = 0.0

    projected = round(state["daily_cost"] + new_cost, 6)

    if projected > state["max_daily_limit"]:
        if raise_on_limit:
            raise RuntimeError(
                f"Daily cost limit exceeded: "
                f"{projected:.4f} > {state['max_daily_limit']}"
            )
        print(f"Daily cost limit exceeded: {projected:.4f} > {state['max_daily_limit']}")

    state["daily_cost"] = projected
    save_cost_state(state)

    return state

print()