<?php

namespace Djshouts;
use Datachore\Type;

class User extends \Datachore\Model
{
	protected $properties = [
		'username'	=> Type::String,
		'email'		=> Type::String,
		'password'	=> Type::String
	];
}
