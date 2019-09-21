function printer_slots()
{
	return ["MainPrinter", "MinorPrinter", "DayPassPrinter"];
}

function printer_logic(badge_info)
{
	var slots = printer_slots();
	if (badge_info.badgeLevel.toLowerCase().includes("day only"))
	{
		return slots[2];
	}
	if (badge_info.ageAtEvent < 18)
	{
		return slots[1];
	}
	return slots[0];
}
