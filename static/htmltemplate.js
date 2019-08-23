/**
 * Render a copy of an HTML <template> tag into another element.
 *
 * A <template> tag should have an "id" attribute that names the template.
 * Each item within the template that can have data applied to it should have
 * a class with the id name, an underscore, then the data name. Example:
 *
 * <template id="templatename">
 *   <div class="templatename_data1"></div>
 *   <div class="templatename_data2"></div>
 * </template>
 *
 * The data object should contain "data1" and "data2".
 *
 * If data_id is supplied any element in the template that matches a data
 * class will have the data_id appended to the class name and set as the
 * id attribute of the element. (".templatename_data1" becomes
 * "#templatename_data1_nnn")
 *
 * @param template_elem The jQuery element that contains the template.
 * @param data A JavaScript object containing the template data.
 * @param data_id Data id to apply to the teplate instance.
 *
 */
function render_html_template(template_elem, data, data_id=null)
{
	template_id = template_elem.attr("id");
	instance_elem = template_elem.clone();

	instance_elem.contents().each(function(idx) {
		for(var key in data)
		{
			let data_class = `.${template_id}_${key}`;
			let full_data_id = data_id === null ? null : `${template_id}_${key}_${data_id}`
			$(this).find(data_class).each(function (idx) {
				if(full_data_id !== null)
				{
					$(this).attr("id", full_data_id);
				}
				$(this).text(data[key]);
			});
		}
	});

	return instance_elem.html(); // There has got to be a better way to do this...
}
