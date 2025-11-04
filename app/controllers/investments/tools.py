duration_map = {
    'monthly' : 30,
    'quarterly' : 91,
    'half_yearly' : 182,
    'yearly' : 365
}

def compute_rate(days: int) -> int:
    """Takes in a duration in days and returns an agreed rate

    Args:
        duration (int): investment duration in days

    Returns:
        int: rate to apply
    """
    monthly = duration_map['monthly']
    quarterly = duration_map['quarterly']
    half_yearly = duration_map['half_yearly']
    yearly = duration_map['yearly']
    rate_map = {
        'monthly': 2,
        'quarterly': 10,
        'half_yearly': 15,
        'yearly': 30
    }


    rate = 0
    if quarterly > days >= monthly:
        rate = rate_map['monthly']
    elif half_yearly > days >= quarterly:
        rate = rate_map['quarterly']
    elif yearly > days >= half_yearly:
        rate = rate_map['half_yearly']
    elif days >= yearly:
        rate = rate_map['yearly']
    
    return rate

# ROI Formula: amount_invested * (interest_rate/100) * months
# 5% * amount_invested * months
# (5/100) * amount_invested * (amount_of_months_since_investment * 30 days)
def compute_roi(investment) -> int:
    rate = compute_rate(investment.duration)
    amount = investment.amount
    roi = ((rate / 100) * amount) + amount
    return roi