<?php

namespace Djshouts;

use Datachore\Type;

class DJ extends \Datachore\Model
{
	protected $properties = [
		'user'		=> Type::Key,
		'name'		=> Type::String,
		'image'		=> Type::Key,
		'homepage'	=> Type::String,
		'bio'		=> Type::String
	];
}
