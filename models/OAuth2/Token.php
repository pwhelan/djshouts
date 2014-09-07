<?php

namespace Deejaypages\OAuth2;

use Datachore\Type;

class Token extends \Datachore\Model
{
	const TYPE_AUTHORIZE = 1;
	const TYPE_ACCESS = 2;
	const TYPE_REFRESH = 3;
	
	protected $properties = [
		'user'		=> Type::Key,
		'token'		=> Type::String,
		'service'	=> Type::Key,
		'type'		=> Type::Integer,
		'scope'		=> Type::String,
		'expires'	=> Type::String
	];
}
