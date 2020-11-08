from django import template

register = template.Library()


def get_page_list(current, total, each_side=2):
    # CC-BY-SA 3.0 by Autumn Leonard (https://stackoverflow.com/a/31836340)

    if total <= (2 * each_side) + 5:
        # in this case, too few pages, so display them all
        start_page = 1
        end_page = total
    elif current <= each_side + 3:
        # in this case, current is too close to the beginning
        start_page = 1
        end_page = (2 * each_side) + 3
    elif current >= total - (each_side + 2):
        # in this case, current is too close to the end
        start_page = total - (2 * each_side) - 2
        end_page = total
    else:
        # regular case
        start_page = current - each_side
        end_page = current + each_side

    pages = []
    if start_page > 1:
        pages.append("1")
    if start_page > 2:
        pages.append("...")
    for x in range(start_page, end_page + 1):
        pages.append(x)
    if end_page < total - 1:
        pages.append("...")
    if end_page < total:
        pages.append(total)
    return pages


@register.simple_tag()
def page_list(page_obj):
    return get_page_list(page_obj.number, page_obj.paginator.num_pages)
