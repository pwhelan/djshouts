<?php

namespace Djshouts;

use Datachore\Type;
use Datachore\Model;


class Show extends Model
{
	protected $properties = [
		/** User reference **/
		'user'		=> Type::Key,
		/** DJ **/
		//'dj'		=> Type::Key,
		/** Recording **/
		//'recording'	=> Type::Key,
		/** Image **/
		'image'		=> Type::Key,
		/** Name **/
		'title'		=> Type::String,
		/** Type (as a string) **/
		'description'	=> Type::String,
		/** URL **/
		'url'		=> Type::String,
		/** Show is Live */
		'is_live'	=> Type::Boolean,
		/** Show Source IP. Used to track offline/switch */
		'source_ip'	=> Type::String,
		/** List of connections */
		'connections'	=> Type::Set
	];
	
	protected function define()
	{
		$this->properties['connections']->type(Type::Key);
	}
}
