from badges import make_template, MODE_GRAYSCALE

@make_template(3.5, 1.125, image_mode=MODE_GRAYSCALE)
def SpecialBadgeTemplate(badge, data):
    badge.register_font('name', 0.375)
    badge.register_font('event', 0.25)
    badge.register_font('info', 0.1875)

    showMinor = False
    if 'staff' in data['badgeLevel'].lower():
        badgeLevel = 'Staff'
    elif 'assistant' in data['badgeLevel'].lower():
        badgeLevel = "Dealer's Assistant"
    else:
        badgeLevel = "Dealer"

    badge.draw.centertext((badge.width / 2, 0.125), data['eventName'], font=badge.font('event'), v_align='top')
    badge.draw.centertext((badge.width / 2, 0.375), data['attendeeBadgeName'], font=badge.font('name'), v_align='top', max_width=3.0)
    badge.draw.centertext((badge.width / 2, 0.875), badgeLevel, font=badge.font('info'), v_align='top')
    if showMinor and data['ageAtEvent'] < 18:
        badge.draw.centertext((0, 0), "MINOR", font=badge.font('info'), v_align='top', h_align='left')
        badge.draw.centertext((badge.width, 0), "MINOR", font=badge.font('info'), v_align='top', h_align='right')
