from badges import make_template

@make_template(3.5, 1.125)
def GenericBadgeTemplate(badge, data):
    badge.register_font('name', 0.375)
    badge.register_font('event', 0.25)
    badge.register_font('info', 0.125)

    badge.draw.centertext((badge.width / 2, 0.125), data['eventName'], font=badge.font('event'), v_align='top')
    badge.draw.centertext((badge.width / 2, 0.375), data['attendeeBadgeName'], font=badge.font('name'), v_align='top', max_width=3.0)
    badge.draw.centertext((0.5, 0.875), data['badgeLevel'], font=badge.font('info'), v_align='top', h_align='left')
    badge.draw.centertext((badge.width - 0.5, 0.875), data['displayId'], font=badge.font('info'), v_align='top', h_align='right')
    if data['ageAtEvent'] < 18:
        badge.draw.centertext((0, 0), "MINOR", font=badge.font('info'), v_align='top', h_align='left')
        badge.draw.centertext((badge.width, 0), "MINOR", font=badge.font('info'), v_align='top', h_align='right')
