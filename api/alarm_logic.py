def logic_a(value):
    if value > 80:
        return "CRITICAL", 1, "Cool down system"
    elif value > 60:
        return "WARN", 1, "Reduce load"
    return "OK", 0, "Normal"

def logic_b(value):
    if value > 120:
        return "CRITICAL", 1, "Release pressure"
    elif value > 90:
        return "WARN", 1, "Monitor pressure"
    return "OK", 0, "Normal"

def logic_c(value):
    if value > 7:
        return "CRITICAL", 1, "Stop machine"
    elif value > 4:
        return "WARN", 1, "Schedule maintenance"
    return "OK", 0, "Normal"