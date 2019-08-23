function update_table(data)
{
	$("#badgeTableBody").empty();
	for(var entry of data)
	{
		var row = $(render_html_template($("#badgeTableRow"), entry, entry.registrantId));
		row.attr("id", entry.registrantId);
		row.next().attr("id", entry.registrantId);
		$("#badgeTableBody").append(row)
	}
	accordion_make($("#badgeTableBody"));
}

function update_search(ev)
{
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
	clear_search();
	$("#updateSearch").click(update_search);
	$("#clearSearch").click(clear_search);
});
