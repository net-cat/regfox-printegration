from badges import make_template, MODE_GRAYSCALE

@make_template(3.5, 1.125, image_mode=MODE_GRAYSCALE)
def TestBadgeTemplate(badge, data):
    badge.register_font('name', 0.375)
    badge.register_font('event', 0.25)
    badge.register_font('info', 0.125)

    badge.draw.centertext((badge.width / 2, 0.125), "NOT VALID", font=badge.font('event'), v_align='top')
    badge.draw.centertext((badge.width / 2, 0.375), "SAMPLE BADGE", font=badge.font('name'), v_align='top', max_width=3.0)
    badge.draw.centertext((0.5, 0.875), data['printerSlot'], font=badge.font('info'), v_align='top', h_align='left')
    badge.draw.centertext((badge.width - 0.5, 0.875), data['printerName'], font=badge.font('info'), v_align='top', h_align='right')
