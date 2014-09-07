<?php

namespace Deejaypages;

use Datachore\Type;
use Datachore\Model;

use google\appengine\api\cloud_storage\CloudStorageTools;

class Image extends Model
{
	protected $properties = [
		'is_public'	=> Type::Boolean,
		'filename'	=> Type::String,
		'url'		=> Type::String,
		'secure_url'	=> Type::String,
		'image_url'	=> Type::String
		// Leave out for now...
		//'original'	=> Type::Key
	];
	
	public function save()
	{
		if (!isset($this->url))
		{
			$this->url = CloudStorageTools::getPublicUrl($this->filename, false);
			$this->image_url = CloudStorageTools::getImageServingUrl(
				$this->filename, []);
		}
		
		if (!isset($this->secure_url))
		{
			$this->secure_url = CloudStorageTools::getPublicUrl($this->filename, true);
		}
		
		parent::save();
	}
}
