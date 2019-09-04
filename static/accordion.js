
/**
 * CSS Classes
 * ac_many - Set on the root element if the accordion should allow multiple items to be open.
 * ac_root - Set on <div> elements to indicate that it is a table root.
 * ac_title - Set on <div>, <li> and <tr> elements to indicate that it is a title element. (Implied on <dt> elements.)
 * ac_data - Set on <div>, <li> and <tr> elements to indicate that it is a data element. (Implied on <dd> elements.)
 * ac_expanded - Set for any title element that has been expandeded.
 * ac_condensed - Set for any title element that has been collapsed.
 * ac_hidden - Set for any data element that is hidden.
 * ac_shown - Set for any data element that is shown.
 * ac_indicator - Any element that has this class will be assigned ac_expanded or ac_condensed instead of its containing title element. (Overrides default behavior.)
 * ac_target - Any element that has this class will be assigned the click() event to expand or collapse the item. (Overrides default behavior.)
 */

/**
 * Turn a <table>, <dl>, <ol> or <ul> element into an accordion.
 *
 * Root elements can be: <table>, <tbody>, <div class="ac_root">, <dl>, <ol> or <ul>.
 * Title elements can be: <tr class="ac_title">, <div class="ac_title>, <dt> or <li class="ac_title">
 * Data elements can be: <tr class="ac_data">, <div class="ac_data">, <dd> or <li class="ac_data">
 *
 * If not using auto_id, data and title elements must have the same id attribute.
 *
 * @param root_elem A jQuery element that will be made into an accordion element.
 * @param auto_id If true, element ids will be numbered sequentially. If false, the id attribute will be used.
 * @returns The ID of the last item in the accordion if auto_id is true, 0 if not.
 */
function accordion_make(root_elem, auto_id=false)
{
	var last_data_id = 0;
	_accordion_all_elements(root_elem).each(function(index) {
		var id = null;
		if (auto_id)
		{
			id = _accordion_element_is_title($(this)) ? ++last_data_id : last_data_id;
		}
		_accordion_element_magic(root_elem, $(this), id);
	});
	return last_data_id;
}

/**
 * Add an item to the beginning of an accordion element.
 *
 * NOTE: Classes ac_data and ac_title will be added to title_elem and root_elem if not present.
 *
 * @param root_elem The jQuery element that has had accordion_make() called on it.
 * @param title_elem A jQuery element containing the <tr>, <dt> or <li> element that will become the title.
 * @param data_elem A jQuery element containing the <tr>, <dd> or <li> element that will become the data.
 * @param new_id The id of the new data. (null will use the title_elem's id attribute.)
 * @returns the id of the new data element.
 */
function accordion_add_item_begin(root_elem, title_elem, data_elem, new_id=null)
{
	_accordion_add_classes_if_needed(title_elem, data_elem);
	new_id = _accordion_element_magic(root_elem, title_elem, new_id);
	_accordion_element_magic(root_elem, data_elem, new_id);
	root_elem.prepend(title_elem, data_elem);
	return new_id;
}

/**
 * Add an item to the end of an accordion element.
 *
 * NOTE: Classes ac_data and ac_title will be added to title_elem and root_elem if not present.
 *
 * @param root_elem The jQuery element that has had accordion_make() called on it.
 * @param title_elem A jQuery element containing the <tr>, <dt> or <li> element that will become the title.
 * @param data_elem A jQuery element containing the <tr>, <dd> or <li> element that will become the data.
 * @param new_id The id of the new data. (null will use the title_elem's id attribute.)
 * @returns the id of the new data element.
 */
function accordion_add_item_end(root_elem, title_elem, data_elem, new_id=null)
{
	_accordion_add_classes_if_needed(title_elem, data_elem);
	new_id = _accordion_element_magic(root_elem, title_elem, new_id);
	_accordion_element_magic(root_elem, data_elem, new_id);
	root_elem.append(title_elem, data_elem);
	return new_id;
}

/**
 * Add an item to an accordion element after the item of the given ID.
 *
 * NOTE: Classes ac_data and ac_title will be added to title_elem and root_elem if not present.
 *
 * @param root_elem The jQuery element that has had accordion_make() called on it.
 * @param target_id The ID of the item after which the element will be inserted.
 * @param title_elem A jQuery element containing the <tr>, <dt> or <li> element that will become the title.
 * @param data_elem A jQuery element containing the <tr>, <dd> or <li> element that will become the data.
 * @param new_id The id of the new data. (null will use the title_elem's id attribute.)
 * @returns the id of the new data element.
 */
function accordion_add_item_after(root_elem, target_id, title_elem, data_elem, new_id=null)
{
	_accordion_add_classes_if_needed(title_elem, data_elem);
	new_id = _accordion_element_magic(root_elem, title_elem, new_id);
	_accordion_element_magic(root_elem, data_elem, new_id);
	_accordion_generate_element_id(root_elem, target_id, true, true).after(title_elem, data_elem);
	return new_id;
}

/**
 * Remove the elements associated with the given ID.
 *
 * @param root_elem The jQuery element that has had accordion_make() called on it.
 * @param id The ID, as returned from accordion_add_item_end or the original element id attribute.
 */
function accorion_remove_item(root_elem, id)
{
	var title_elem = accordion_get_title_elem(root_elem, id);
	var data_elem = accordion_get_data_elem(root_elem, id);

	if (title_elem)
	{
		title_elem.remove();
	}

	if (data_elem)
	{
		data_elem.remove();
	}
}

/**
 * Replace the element with the given id with a new element. Previous state is maintained.
 *
 * @param root_elem The jQuery element that has had accordion_make() called on it.
 * @param id The ID, as returned from accordion_add_item_end or the original element id attribute, of the attribute to replace.
 * @param new_title_elem The new title element.
 * @param new_data_elem The new data element.
 * @param new_id The id of the new data. (null will use the title_elem's id attribute, false will use id.)
 * @returns true if replacement was successful, false if not.
 */
function accordion_replace_item(root_elem, id, new_title_elem, new_data_elem, new_id=false)
{
	var title_elem = accordion_get_title_elem(root_elem, id);
	var data_elem = accordion_get_data_elem(root_elem, id);

	if (!title_elem || !data_elem)
	{
		return false;
	}

	if (new_id === false)
	{
		new_id = id;
	}

	new_id = _accordion_element_magic(root_elem, new_title_elem, new_id);
	_accordion_element_magic(root_elem, new_data_elem, new_id);
	data_elem.after(new_title_elem, new_data_elem);
	var old_elem_state = _accordion_title_is_expanded(title_elem);
	title_elem.remove();
	data_elem.remove();
	_accordion_set_item_state(new_title_elem, new_data_elem, root_elem, old_elem_state);
}

/**
 * Get the current state of the given item.
 *
 * @param root_elem The jQuery element that has had accordion_make() called on it.
 * @param id The ID, as returned from accordion_add_item_end or the original element id attribute.
 * @returns the current state.
 */
function accordion_get_item_state(root_elem, id)
{
	var title_elem = _accordion_generate_element_id(root_elem, id, false, true);
	return _accordion_title_is_expanded(title_elem);
}

/**
 * Set or toggle the state of an item of an accordion element.
 *
 * @param root_elem The jQuery element that has had accordion_make() called on it.
 * @param id The ID, as returned from accordion_add_item_end or the original element id attribute.
 * @param new_state true=expanded, false=collapse, null=toggle
 * @returns the previous state.
 */
function accordion_set_item_state(root_elem, id, new_state=null)
{
	var title_elem = _accordion_generate_element_id(root_elem, id, false, true);
	var data_elem = _accordion_generate_element_id(root_elem, id, true, true);
	var old_state = _accordion_title_is_expanded(title_elem);
	_accordion_set_item_state(title_elem, data_elem, root_elem, new_state);
	return old_state;
}

/**
 * Return the jQuery title (<tr>, <li> or <dt>) element for the given id from an accordion alement.
 *
 * @param root_elem The jQuery element that has had accordion_make() called on it.
 * @param id The ID, as returned from accordion_add_item_end or the original element id attribute.
 * @returns the title element.
 */
function accordion_get_title_elem(root_elem, id)
{
	return _accordion_generate_element_id(root_elem, id, false, true);
}

/**
 * Return the jQuery data (<tr>, <li> or <dd>) element for the given id from an accordion alement.
 *
 * @param root_elem The jQuery element that has had accordion_make() called on it.
 * @param id The ID, as returned from accordion_add_item_end or the original element id attribute.
 * @returns the data element.
 */
function accordion_get_data_elem(root_elem, id)
{
	return _accordion_generate_element_id(root_elem, id, true, true);
}

/**
 * Collapse all items in the given accordion element.
 *
 * @param root_elem The jQuery element that has had accordion_make() called on it.
 */
function accordion_collapse_all(root_elem)
{
	_accordion_all_elements(root_elem).each(function(index) {
		_accordion_set_element_state($(this), false);
	});
}

/**
 * Expand all items in the given accordion element that has ac_many set
 *
 * @param root_elem The jQuery element that has had accordion_make() called on it.
 */
function accordion_expand_all(root_elem)
{
	if(_accordion_many(root_elem))
	{
		_accordion_all_elements(root_elem).each(function(index) {
			_accordion_set_element_state($(this), true);
		});
	}
}

// ----- Internal Functions -----

/// Given a title and data element, add ac_title and ac_data if they are not already present.
function _accordion_add_classes_if_needed(title_elem, data_elem)
{
	if (title_elem !== null && (title_elem.prop("tagName") == "TR" || title_elem.prop("tagName") == "LI" || title_elem.prop("tagName") == "DIV") && !title_elem.hasClass("ac_title"))
	{
		title_elem.addClass("ac_title");
	}
	if (data_elem !== null && (data_elem.prop("tagName") == "TR" || data_elem.prop("tagName") == "LI" || data_elem.prop("tagName") == "DIV") && !data_elem.hasClass("ac_data"))
	{
		data_elem.addClass("ac_data");
	}
}

/// Generate an element id given the root element and the data_id and whether it is data or title.
/// If get_elem, is true, the return will be a jQuery object against the generated ID.
function _accordion_generate_element_id(root_elem, data_id, is_data, get_elem=false)
{
	var accordion_id = root_elem.attr("id");
	var id_type = is_data ? "data" : "title";
	var id_name = `${accordion_id}_${id_type}_${data_id}`;
	if (get_elem)
	{
		return $("#".concat(id_name));
	}
	return id_name;
}

/// Query all accordion elements within a root element.
function _accordion_all_elements(root_elem)
{
	return root_elem.find("dt,dd,tr,li,div");
}

/// Element is <dt> or has "ac_title" class
function _accordion_element_is_title(elem)
{
	return elem.prop("tagName") == "DT" || elem.hasClass("ac_title");
}

/// Element is <dd> or has "ac_data" class
function _accordion_element_is_data(elem)
{
	return elem.prop("tagName") == "DD" || elem.hasClass("ac_data");
}

/// Modify the given element with the root element to be a functional part of the accordion
function _accordion_element_magic(root_elem, elem, id=null)
{
	var data_id = id === null ? elem.attr("id") : id;
	var elem_props = {"root_elem": root_elem, "data_id": data_id};

	if (_accordion_element_is_title(elem))
	{
		elem.attr("id", _accordion_generate_element_id(root_elem, data_id, false));

		let targets = elem.find(".ac_target");
		if (!targets.length)
		{
			targets = [elem];
		}
		$.each(targets, function(index) {
			$(this).click(elem_props, _accordion_toggle_item_event);
		});

	}
	else if (_accordion_element_is_data(elem))
	{
		elem.attr("id", _accordion_generate_element_id(root_elem, data_id, true));
	}

	_accordion_set_element_state(elem, false);
	return data_id;
}

/// Find indicator elements
function _accordion_find_indicators(elem)
{
	let indicators = elem.find(".ac_indicator");

	if (_accordion_element_is_title(elem) && !indicators.length)
	{
		indicators = [elem];
	}

	return indicators;
}

/// Set the appropitate classes on the element for the requested expansion state.
function _accordion_set_element_state(elem, is_expanded)
{
	$.each(_accordion_find_indicators(elem), function(index) {
		if (is_expanded)
		{
			$(this).addClass("ac_expanded");
			$(this).removeClass("ac_condensed");
		}
		else
		{
			$(this).addClass("ac_condensed");
			$(this).removeClass("ac_expanded");
		}
	});

	if (_accordion_element_is_data(elem))
	{
		if (is_expanded)
		{
			elem.removeClass("ac_hidden");
			elem.addClass("ac_shown");
		}
		else
		{
			elem.addClass("ac_hidden");
			elem.removeClass("ac_shown");
		}
	}
}

/// True if the title element has been expanded
function _accordion_title_is_expanded(title_elem)
{
	var indicators = _accordion_find_indicators(title_elem);

	if (!indicators.length)
	{
		return false;
	}

	var indicator = $(indicators[0]);
	return !indicator.hasClass("ac_condensed") || indicator.hasClass("ac_expanded");
}

/// Click event handler for title.
function _accordion_toggle_item_event(ev)
{
	accordion_set_item_state(ev.data.root_elem, ev.data.data_id);
}

/// Check to see if the accordion root tag has ac_many set.
function _accordion_many(root_elem)
{
	return root_elem.hasClass("ac_many");
}

/// Backend for accordion_set_item_state. (Used in a few places...)
function _accordion_set_item_state(title_elem, data_elem, root_elem, new_state=null)
{
	new_state = new_state === null ? !_accordion_title_is_expanded(title_elem) : new_state;

	if (_accordion_many(root_elem))
	{
		_accordion_set_element_state(data_elem, new_state);
		_accordion_set_element_state(title_elem, new_state);
	}
	else
	{
		if (new_state && !_accordion_title_is_expanded(title_elem))
		{
			accordion_collapse_all(root_elem);
			_accordion_set_element_state(data_elem, true);
			_accordion_set_element_state(title_elem, true);
		}
		else if (!new_state)
		{
			_accordion_set_element_state(data_elem, false);
			_accordion_set_element_state(title_elem, false);
		}
	}
}
