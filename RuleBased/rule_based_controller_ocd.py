def get_total_queue(state):
    """Tổng xe đang dừng trên mọi lane của TLS đang control."""
    tls = next(iter(state["tls"].values()))
    return tls["totals"]["halting_count"]


def choose_action(state):
    """
    Rule đơn giản cho O Cho Dùa (4 green stages):
    - Giữ tối thiểu min_green (30s)
    - Bắt buộc SWITCH khi đạt max_green (75s)
    - Nếu đã xanh khá lâu mà queue tổng còn thấp → SWITCH
    """
    tls = next(iter(state["tls"].values()))

    if tls.get("in_transition"):
        return "KEEP"

    green_elapsed = tls.get("green_elapsed", 0)
    if green_elapsed < 30:
        return "KEEP"
    if green_elapsed >= 75:
        return "SWITCH"
    
    
    total_queue = get_total_queue(state)

    if green_elapsed >= 45 and total_queue >= 25:
        return "SWITCH"
    
    if green_elapsed >= 50 and total_queue <= 5:
        return "SWITCH"
    
    return "KEEP"