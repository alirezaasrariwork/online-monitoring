def evaluate_signal(value, thresholds):
    """
    thresholds: dict with keys 'critical', 'warning', 'normal'
    returns: level, suggestion, critical_suggest, warning_suggest, normal_suggest
    """
    critical, warning, normal = thresholds['critical'], thresholds['warning'], thresholds['normal']

    if value >= critical:
        level = "Critical"
        suggestion = "🚨 Immediate action required!"
    elif value >= warning:
        level = "Warning"
        suggestion = "⚠️ Check system soon"
    else:
        level = "Normal"
        suggestion = "✅ System operating normally"

    # Example logic for three suggestion columns
    critical_suggest = f"Critical logic applied: threshold={critical}"
    warning_suggest = f"Warning logic applied: threshold={warning}"
    normal_suggest = f"Normal logic applied: threshold={normal}"

    return level, suggestion, critical_suggest, warning_suggest, normal_suggest
