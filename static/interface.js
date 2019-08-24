function update_table(data)
{
	$("#badgeTableBody").empty();
	for(var entry of data)
	{
		tpl = $.templates("#badgeTableRow");
		var row = tpl.render(entry);
		$("#badgeTableBody").append(row);
	}
	accordion_make($("#badgeTableBody"));
}

function update_search(ev)
{
	if (ev.type == "keypress" && event.which != 13)
	{
		return;
	}
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

$(document).ready(function (){
	$("#searchBox").keypress(update_search);
	clear_search();
	$("#updateSearch").click(update_search);
	$("#clearSearch").click(clear_search);
});
