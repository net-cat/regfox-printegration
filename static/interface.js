var columns = [
	"registrantId",
	"displayId",
	"orderId",
	"badgeLevel",
	"status",
	"firstName",
	"lastName",
	"email",
	"attendeeBadgeName",
	"dateOfBirth",
	"phone",
	"billingCountry",
	"billingZip",
	"checkedIn"
];

var display_columns = {
	"attendeeBadgeName": "Badge Name",
	"firstName": "First Name",
	"lastName": "Last Name",
	"badgeLevel": "Badge Level",
	"status": "Order Status"
};

var extended_display_columns = {
	"email": "Email",
	"dateOfBirth": "Birthday",
	"phone": "Phone Number",
	"billingZip": "Zip Code",
	"billingCountry": "Country"
};

function show_extended(registrant_id, show)
{
	var entry = $("#entryinfo".concat(registrant_id));
	if(show)
	{
		entry.removeClass("hidden");
	}
	else
	{
		entry.addClass("hidden");
	}
}

function update_table(data)
{
	var table_html = "";
	colspan = Object.keys(display_columns).length + 1;

	$("#badgeTable").find("tbody").empty();
	for(var entry of data)
	{
		var row = $("<tr>").attr("id", "entry".concat(entry.registrantId));
		row.append($("<td>").append($("<a>").text("Show").attr("href", "#").click(entry.registrantId, function(e){ e.preventDefault(); show_extended(e.data, true); })))
		for(var name in display_columns)
		{
			row.append($("<td>").text(entry[name]));
		}
		$("#badgeTable").find("tbody").append(row);

		var elist = $("<ul>");
		for(var name in extended_display_columns)
		{
			elist.append($("<li>").text(entry[name]));
		}
		var ecol = $("<td>").attr("colspan", colspan);
		ecol.append(elist);
		ecol.append($("<a>").text("Hide").attr("href", "#").click(entry.registrantId, function(e){ e.preventDefault(); show_extended(e.data, false); }));
		$("#badgeTable").find("tbody").append($("<tr>").attr("id", "entryinfo".concat(entry.registrantId)).attr("class", "hidden").append(ecol));

	}

}

function start_interface()
{
	var header = $("<tr>").append("<td>");
	for(var name in display_columns)
	{
		var header_col = $("<td>");
		header_col.text(display_columns[name]);
		header.append(header_col);
	}
	$("#badgeTable").find("thead").append(header);
	$.getJSON("/query", update_table);
}
