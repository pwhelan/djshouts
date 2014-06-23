$(document).ready(function() {
	if (typeof radios != 'undefined')
	{
		$('#id_url').autocomplete({ source: radios });
	}
});
