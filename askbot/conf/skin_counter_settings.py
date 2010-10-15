"""
Skin settings to color view, vote and answer counters
"""
from askbot.conf.settings_wrapper import settings
from askbot.deps.livesettings import ConfigurationGroup, IntegerValue, StringValue
from django.utils.translation import ugettext as _
from askbot.deps.grapefruit import Color

SKIN_COUNTER_SETTINGS = ConfigurationGroup(
                            'SKIN_COUNTER_SETTINGS',
                            _('Skin: view, vote and answer counters')
                        )

settings.register(
    IntegerValue(
        SKIN_COUNTER_SETTINGS,
        'VOTE_COUNTER_EXPECTED_MAXIMUM',
        default=3,
        description=_('Vote counter value to give "full color"'),
        hidden=True,
    )
)

settings.register(
    StringValue(
        SKIN_COUNTER_SETTINGS,
        'COLORS_VOTE_COUNTER_EMPTY_BG',
        default='white',
        description=_('Background color for votes = 0'),
        help_text=_('HTML color name or hex value'),
        hidden=True,
    )
)

settings.register(
    StringValue(
        SKIN_COUNTER_SETTINGS,
        'COLORS_VOTE_COUNTER_EMPTY_FG',
        default='gray',
        description=_('Foreground color for votes = 0'),
        help_text=_('HTML color name or hex value'),
        hidden=True,
    )
)

settings.register(
    StringValue(
        SKIN_COUNTER_SETTINGS,
        'COLORS_VOTE_COUNTER_MIN_BG',
        default='#a3d0ff',
        description=_('Background color for votes'),
        help_text=_('HTML color name or hex value')
    )
)

settings.register(
    StringValue(
        SKIN_COUNTER_SETTINGS,
        'COLORS_VOTE_COUNTER_MIN_FG',
        default='#4a4a4a',
        description=_('Foreground color for votes'),
        help_text=_('HTML color name or hex value')
    )
)

settings.register(
    StringValue(
        SKIN_COUNTER_SETTINGS,
        'COLORS_VOTE_COUNTER_MAX_BG',
        default='#a9d0f5',
        description=_('Background color for votes = MAX'),
        help_text=_('HTML color name or hex value'),
        hidden=True,
    )
)

settings.register(
    StringValue(
        SKIN_COUNTER_SETTINGS,
        'COLORS_VOTE_COUNTER_MAX_FG',
        default=Color.NewFromHtml(
                        '#a9d0f5'
                    ).DarkerColor(0.7).html,
        description=_('Foreground color for votes = MAX'),
        help_text=_('HTML color name or hex value'),
        hidden=True,
    )
)

settings.register(
    IntegerValue(
        SKIN_COUNTER_SETTINGS,
        'VIEW_COUNTER_EXPECTED_MAXIMUM',
        default=100,
        description=_('View counter value to give "full color"'),
        hidden=True,
    )
)

settings.register(
    StringValue(
        SKIN_COUNTER_SETTINGS,
        'COLORS_VIEW_COUNTER_EMPTY_BG',
        default='gray',
        description=_('Background color for views = 0'),
        help_text=_('HTML color name or hex value'),
        hidden=True,
    )
)

settings.register(
    StringValue(
        SKIN_COUNTER_SETTINGS,
        'COLORS_VIEW_COUNTER_EMPTY_FG',
        default='white',
        description=_('Foreground color for views = 0'),
        help_text=_('HTML color name or hex value'),
        hidden=True,
    )
)

settings.register(
    StringValue(
        SKIN_COUNTER_SETTINGS,
        'COLORS_VIEW_COUNTER_MIN_BG',
        default='#ff8c8c',
        description=_('Background color for views'),
        help_text=_('HTML color name or hex value')
    )
)

settings.register(
    StringValue(
        SKIN_COUNTER_SETTINGS,
        'COLORS_VIEW_COUNTER_MIN_FG',
        default='#4a4a4a',
        description=_('Foreground color for views'),
        help_text=_('HTML color name or hex value')
    )
)

settings.register(
    StringValue(
        SKIN_COUNTER_SETTINGS,
        'COLORS_VIEW_COUNTER_MAX_BG',
        default='#FF8000',
        description=_('Background color for views = MAX'),
        help_text=_('HTML color name or hex value'),
        hidden=True,
    )
)

settings.register(
    StringValue(
        SKIN_COUNTER_SETTINGS,
        'COLORS_VIEW_COUNTER_MAX_FG',
        default=Color.NewFromHtml(
                            '#ff8000'
                        ).DarkerColor(
                            0.7
                        ).html,
        description=_('Foreground color for views = MAX'),
        help_text=_('HTML color name or hex value'),
        hidden=True,
    )
)

settings.register(
    IntegerValue(
        SKIN_COUNTER_SETTINGS,
        'ANSWER_COUNTER_EXPECTED_MAXIMUM',
        default=4,
        description=_('Answer counter value to give "full color"'),
        hidden=True,
    )
)

settings.register(
    StringValue(
        SKIN_COUNTER_SETTINGS,
        'COLORS_ANSWER_COUNTER_EMPTY_BG',
        default=Color.NewFromHtml('#a40000').Blend(
                                Color.NewFromHtml('white'),0.8
                            ).html,
        description=_('Background color for answers = 0'),
        help_text=_('HTML color name or hex value'),
    )
)

settings.register(
    StringValue(
        SKIN_COUNTER_SETTINGS,
        'COLORS_ANSWER_COUNTER_EMPTY_FG',
        default='yellow',
        description=_('Foreground color for answers = 0'),
        help_text=_('HTML color name or hex value'),
    )
)

settings.register(
    StringValue(
        SKIN_COUNTER_SETTINGS,
        'COLORS_ANSWER_COUNTER_MIN_BG',
        default='#ffed9c',
        description=_('Background color for answers'),
        help_text=_('HTML color name or hex value')
    )
)

settings.register(
    StringValue(
        SKIN_COUNTER_SETTINGS,
        'COLORS_ANSWER_COUNTER_MIN_FG',
        default='#a4a4a4',
        description=_('Foreground color for answers'),
        help_text=_('HTML color name or hex value')
    )
)

settings.register(
    StringValue(
        SKIN_COUNTER_SETTINGS,
        'COLORS_ANSWER_COUNTER_MAX_BG',
        default=Color.NewFromHtml('#61380B').Blend(
                            Color.NewFromHtml('white'),0.75
                                                    ).html,
        description=_('Background color for answers = MAX'),
        help_text=_('HTML color name or hex value'),
        hidden=True,
    )
)

settings.register(
    StringValue(
        SKIN_COUNTER_SETTINGS,
        'COLORS_ANSWER_COUNTER_MAX_FG',
        default='#ffff00',
        description=_('Foreground color for answers = MAX'),
        help_text=_('HTML color name or hex value'),
        hidden=True,
    )
)

settings.register(
    StringValue(
        SKIN_COUNTER_SETTINGS,
        'COLORS_ANSWER_COUNTER_ACCEPTED_BG',
        default=Color.NewFromHtml('darkgreen').Blend(
                                    Color.NewFromHtml('white'),0.8
                                                    ).html,
        description=_('Background color for accepted'),
        help_text=_('HTML color name or hex value')
    )
)

settings.register(
    StringValue(
        SKIN_COUNTER_SETTINGS,
        'COLORS_ANSWER_COUNTER_ACCEPTED_FG',
        default='#D0F5A9',
        description=_('Foreground color for accepted answer'),
        help_text=_('HTML color name or hex value')
    )
)
