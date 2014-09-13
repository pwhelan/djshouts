<?php

namespace Djshouts;

use Datachore\Type;
use Datachore\Model;

use google\appengine\api\cloud_storage\CloudStorageTools;

class Image extends Model
{
	protected $properties = [
		//'is_public'	=> Type::Boolean,
		'filename'	=> Type::String,
		'url'		=> Type::String,
		'secure_url'	=> Type::String,
		'image_url'	=> Type::String,
		'user'		=> Type::Key
	];
	
	// $mutation is Ignored!
	public function save($mutation = null)
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
	
	public function crop($size)
	{
		$cropped = Image\URL::where('parent', '==', $this->__key)
			->andWhere('size', '==', $size)
			->first();
		
		if (!$cropped)
		{
			$cropped = new Image\URL;
			$cropped->size = $size;
			$cropped->parent = $this;
			$cropped->save();
		}
		
		return $cropped;
	}
	
	public function getUrl()
	{
		if (\Environment::isAppEngine() && 0)
		{
			return $this->url;
		}
		else
		{
			return $this->image_url;
		}
	}
}
