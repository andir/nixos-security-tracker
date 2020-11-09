import random

import pytest

from tracker.templatetags.pagination import get_page_list


# TODO: Use python-quickcheck when https://github.com/t2y/pytest-quickcheck/issues/15 is fixed
# @pytest.mark.randomize(total=int, min_num=0, max_num=100, ncalls=10)
def test_page_list(total: int = 15) -> None:
    current = random.randrange(1, total)
    pages = get_page_list(current, total)

    # starts with 1
    assert pages[0] == 1

    # ends with total
    assert pages[-1] == total

    # we can have at most two dots
    dots = [i for i, page in enumerate(pages) if page == "..."]
    assert len(dots) <= 2

    # dots are warranted
    for dot in dots:
        left, right = pages[dot - 1], pages[dot + 1]
        assert left + 1 < right

    # pages are in order
    sequence = [page for page in pages if page != "..."]
    assert sequence == sorted(sequence)
