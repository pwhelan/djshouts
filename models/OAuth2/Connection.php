<?php

namespace Djshouts\OAuth2;

use Datachore\Type;
use Datachore\Model;


class Connection extends Model
{
	protected $properties = [
		/** User reference **/
		'user'		=> Type::Key,
		/** Service Reference **/
		'service'	=> Type::Key,
		/** External ID **/
		'xid'		=> Type::String,
		/** Name **/
		'name'		=> Type::String,
		/** Type (as a string) **/
		'type'		=> Type::String,
		/** Is Hidden ? **/
		'is_hidden'	=> Type::Boolean
	];
}
