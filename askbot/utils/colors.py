from askbot.deps.grapefruit import Color
import keyedcache
import math

@keyedcache.cache_function(length=6000)
def get_counter_colors(count, counter_max=10, empty_bg='white', empty_fg='black', 
                        zero_bg='white', zero_fg='black',
                        min_bg='white', min_fg='black',
                        max_bg='white', max_fg='black'
                        ):
    if count == 0:
        return zero_fg, zero_bg

    if count > counter_max:
        blend_factor = 0
    else:
        #todo deal with negative counts properly
        blend_factor = 1 - math.fabs(float(count)/float(counter_max))

    max_fg_color = Color.NewFromHtml(max_fg)
    fg = Color.NewFromHtml(min_fg).Blend(max_fg_color, blend_factor)

    max_bg_color = Color.NewFromHtml(max_bg)
    bg = Color.NewFromHtml(min_bg).Blend(max_bg_color, blend_factor)

    return fg.html, bg.html
