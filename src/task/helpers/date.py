from datetime import date


def is_out_of_deadline(deadline: date) -> bool:
    now = date.today()
    if deadline and deadline < now:
        return True
    return False

