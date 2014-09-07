/*
* JavaScript Load Image Demo JS 1.9.1
* https://github.com/blueimp/JavaScript-Load-Image
*
* Copyright 2013, Sebastian Tschan
* https://blueimp.net
*
* Licensed under the MIT license:
* http://www.opensource.org/licenses/MIT
*/

/*global window, document, loadImage, HTMLCanvasElement, $ */

$(function () {
	'use strict';
	
	var result = $('#canvas'),
		currentFile,
	
	replaceResults = function (img) {
		var content;
		
		img = loadImage.scale(
			img,
			{maxWidth: 800, maxHeight: 1000}
		);
		
		if (!(img.src || img instanceof HTMLCanvasElement)) {
			content = $('<span>Loading image file failed</span>');
		} else {
			content = $('<a target="_blank">').append(img)
			.attr('download', currentFile.name)
			.attr('href', img.src || img.toDataURL());
		}
		result.children().replaceWith(content);
		if (img.getContext) {
			//actionsNode.show();
		}
	},
	displayImage = function (file, options) {
		
		currentFile = file;
		if (!loadImage(file, replaceResults, options))
		{
			console.log("LOADED");
			result.children().replaceWith(
				$('<span>Your browser does not support the URL or FileReader API.</span>')
			);
		}
	},
	dropChangeHandler = function (e) {
		
		e.preventDefault();
		e = e.originalEvent;
		var target = e.dataTransfer || e.target,
			file = target && target.files && target.files[0],
			options = { canvas: true };
		if (!file) {
			console.log('NO FILE');
			return;
		}
		loadImage.parseMetaData(file, function (data) {
			console.log('PARSED');
			displayImage(file, options);
		});
	},
	coordinates;

	// Hide URL/FileReader API requirement message in capable browsers:
	$(document)
		.on('dragover', function (e) {
			e.preventDefault();
			e = e.originalEvent;
			e.dataTransfer.dropEffect = 'copy';
		})
		.on('drop', dropChangeHandler);
	
	$('#canvas-input').on('change', dropChangeHandler);
	
});

$('input').on('change keyup paste', function() {
	var alerts = $('div.alert');

	if (!alerts.hasClass('danger') || alerts.length <= 0)
	{
		alerts.remove();
		$('form').before('<div class="alert alert-danger" role="alert">Unsaved changes, please save</div>');
	}
});

$(document).ready(function() {
	
	$('form').submit(function() {
		
		$('div.alert').remove();

		var fd = new FormData($('#service')[0]);
		var canvas = $('#canvas a');
		var image_id = $('#image_id');
		
		
		if (image_id.val())
		{
			fd.append('id', image_id.val());
		}
		
		if (canvas.length > 0)
		{
			fd.append(
				'image',
				dataURLtoBlob(canvas.attr('href'))
			);
		}
		$.ajax({
			processData: 	false,
			contentType: 	false,
			type: 		'POST',
			url: 		upload_url,
			data: 		fd, // dataURLtoBlob($('#dj-picture a').attr('href')),
			success: 	function(result) {
				upload_url = result.upload_url;
				image_id.val(result.image.id);
				//$('form').before('<div class="alert alert-success" role="alert">Saved!</div>');
				return false;
			}
		});

		return false;
	});
});
