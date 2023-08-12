from entities.tip import Tip


def sort_tips(tips: list[Tip], sort_method="recent"):
    if sort_method == "rating":
        reverse = True
        key = rating
    elif sort_method == "oldest":
        reverse = False
        key = creation_time
    else:  # sort_method == "recent"
        reverse = True
        key = creation_time

    tips.sort(reverse=reverse, key=key)


def creation_time(tip):
    return tip.creation_time


def rating(tip):
    return tip.rating
