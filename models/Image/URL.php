<?php

namespace Djshouts\Image;

use Datachore\Type;
use Datachore\Model;

use google\appengine\api\cloud_storage\CloudStorageTools;

class URL extends Model
{
	protected $properties = [
		'parent'	=> Type::Key,
		'size'		=> Type::Integer,
		'url'		=> Type::String
	];
	
	public function save()
	{
		if (!$this->url)
		{
			$this->url = CloudStorageTools::getImageServingUrl(
				$this->foreign['parent']->filename, [
					'crop'	=> true,
					'size'	=> isset($this->updates['size']) ?
						$this->updates['size'] :
						(int)(string)$this->values['size']
				]);
		}
		
		parent::save();
	}
}
