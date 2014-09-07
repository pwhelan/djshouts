$( "#title" ).autocomplete({
	source: _.uniq(
		$.map(Shows, function(show, i) {
			return show.title;
		}),
		false,
		function(title) {
			return title.toLowerCase();
		}
	),
	messages: {
		noResults: '',
		results: function() {}
	}
});

$( "#url" ).autocomplete({
	source: _.uniq(
		$.map(Shows, function(show, i) {
			return show.url;
		}),
		false,
		function(title) {
			return title.toLowerCase();
		}
	),
	messages: {
		noResults: '',
		results: function() {}
	}
});
