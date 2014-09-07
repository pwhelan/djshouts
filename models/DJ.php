<?php

namespace Djshouts;

use Datachore\Type;

class DJ extends \Datachore\Model
{
	protected $properties = [
		'name'		=> Type::String,
		'picture'	=> Type::String,
		'user'		=> Type::Key
	];
}
