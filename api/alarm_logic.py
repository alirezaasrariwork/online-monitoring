def logic_a(value):
    if value > 80:
        return "CRITICAL", True, "Cool down system"
    elif value > 60:
        return "WARN", True, "Reduce load"
    return "OK", False, "Normal"

def logic_b(value):
    if value > 120:
        return "CRITICAL", True, "Release pressure"
    elif value > 90:
        return "WARN", True, "Monitor pressure"
    return "OK", False, "Normal"

def logic_c(value):
    if value > 7:
        return "CRITICAL", True, "Stop machine"
    elif value > 4:
        return "WARN", True, "Schedule maintenance"
    return "OK", False, "Normal"
