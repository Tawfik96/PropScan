import json
from datetime import datetime

try:
    from .paths import COST_FILE
except ImportError:
    from paths import COST_FILE


def load_cost_state():
    if not COST_FILE.exists():
        return {
            "date": datetime.now().date().isoformat(),
            "daily_cost": 0.0,
            "max_daily_limit": 2.0
        }

    with COST_FILE.open("r") as f:
        return json.load(f)


def save_cost_state(state):
    with COST_FILE.open("w") as f:
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
