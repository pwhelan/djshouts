<?php

namespace Djshouts\Radio;

use Datachore\Model;
use Datachore\Type;

class Stat extends Model
{
	protected $properties = [
		'timestamp'	=> Type::Timestamp,
		'show'		=> Type::Key,
		'listeners'	=> Type::Integer,
		'description'	=> Type::String,
		'title'		=> Type::String
	];
}
