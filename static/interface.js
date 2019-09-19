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
		$(this).click(function(ev){
			$.getJSON(`/print_badge?id=${entry.registrantId}`);
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
	$.getJSON(`/print_badge?id=${entry.registrantId}`);
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

function populate_printer_table(data)
{
	for(var slot of printer_slots())
	{
		tpl = $.templates("#printerTableRow");
		var row = tpl.render({
			"slotName": slot,
			"slotSelectorName": "selector".concat(slot),
			"printers": data,
		});
		$("#printerTable").append(row);
	}
}

$(document).ready(function (){
	$("#searchBox").keypress(update_search);
	clear_search();
	$("#updateSearch").click(update_search);
	$("#clearSearch").click(clear_search);
	$.getJSON("/printer_list", populate_printer_table);
});
