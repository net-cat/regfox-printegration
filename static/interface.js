function render_registrant(entry)
{
	tpl = $.templates("#badgeTableRow");
	var row = $(tpl.render(entry));
	row.find(`#checkin_${entry.registrantId}`).each(function(index){
		let badge_id = entry.registrantId;
		$(this).click(function(ev){
			$.getJSON(`/checkin_badge?id=${badge_id}`, update_entry_and_print);
		});
	});
	row.find(`#update_${entry.registrantId}`).each(function(index){
		let badge_id = entry.registrantId;
		$(this).click(function(ev){
			$.getJSON(`/update_badge?id=${badge_id}`, update_entry);
		});
	});
	row.find(`#reprint_${entry.registrantId}`).each(function(index){
		let badge_id = entry.registrantId;
		let slot_name = printer_logic(entry);
		$(this).click(function(ev){
			var printer_name = slot_to_name(slot_name);
			$.getJSON(`/print_badge?id=${entry.registrantId}&name=${printer_name}`);
		});
	});
	return row;
}

function update_entry(entry)
{
	if(entry === false)
	{
		alert(String.prototype.concat(
			"Registrant not found or registration is not completed.\n\n",
			"If they just registered, their data may not have been pulled in yet.\n",
			"If they just paid, click the Update button and try again."
		));
		return false;
	}
	var row = render_registrant(entry);
	var title_elem = row.first();
	var data_elem = title_elem.next();
	accordion_replace_item($("#badgeTable"), entry.registrantId, title_elem, data_elem);
	return true;
}

function update_entry_and_print(entry)
{
	if(!update_entry(entry))
	{
		return;
	}
	let printer_name = slot_to_name(printer_logic(entry));
	$.getJSON(`/print_badge?id=${entry.registrantId}&name=${printer_name}`);
}

function update_table(data)
{
	$("#badgeTable").empty();
	for(var entry of data)
	{
		$("#badgeTable").append(render_registrant(entry));
	}
	accordion_make($("#badgeTable"));
}

function update_search(ev)
{
	if (ev.type == "keypress" && event.which != 13)
	{
		$("#updateSearch").attr("value", "Search");
		return;
	}
	ev.preventDefault();
	$("#updateSearch").attr("value", "Reload");
	var new_search = $("#searchBox").val();
	var criteria = encodeURIComponent(new_search);
	var query = `/query?criteria=${criteria}`;
	$.getJSON(query, update_table);
}

function clear_search(ev=null)
{
	$("#searchBox").val("");
	$.getJSON("/query", update_table);
}

function make_slot_selector_name(slot)
{
	return "selector".concat(slot);
}

function print_test(printer_name, printer_slot)
{
	var query = `/print_test?name=${printer_name}&slot=${printer_slot}`;
	$.getJSON(query);
}

function populate_printer_table(data)
{
	for(var slot of printer_slots())
	{
		var selector_name = make_slot_selector_name(slot)
		var tpl = $.templates("#printerTableRow");
		var row = $(tpl.render({
			"slotName": slot,
			"slotSelectorName": selector_name,
			"printers": data,
		}));
		row.find("#testprint_".concat(slot)).click(slot, function(ev) {
			print_test(slot_to_name(ev.data), ev.data);
		})
		$("#printerTable").append(row);
	}
}

function slot_to_name(slot)
{
	var selector = "#".concat(make_slot_selector_name(slot), " option:selected");
	var option_elem = $(selector);
	if (option_elem.length == 0)
	{
		return "null"; // Yes, string "null", not JS null.
	}
	return option_elem.attr("value");
}

$(document).ready(function (){
	$("#searchBox").keypress(update_search);
	clear_search();
	$("#updateSearch").click(update_search);
	$("#clearSearch").click(clear_search);
	$.getJSON("/printer_list", populate_printer_table);
});
