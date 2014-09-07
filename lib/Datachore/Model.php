<?php

/** @TODO:
 *    * Allow setting keys directly with models and not with their keys, ie:
 *      $object->ref = $ref instead of $object->ref = $ref->key.
 */
namespace Datachore;

class Model extends Datachore
{
	/** private super key **/
	protected $__key = null;
	
	/** Property definitions **/
	protected $properties = [];
	
	/** Property Values **/
	protected $values = [];
	
	/** Changed values **/
	protected $updates = [];
	
	/** Foreign Objects **/
	protected $foreign = [];
	
	
	public function __get($key)
	{
		if ($key == 'id')
		{
			if ($this->__key)
			{
				return $this->__key->getPathElement(0)->getId();
			}
			else
			{
				return null;
			}
		}
		else if ($key == 'key')
		{
			return $this->__key;
		}
		else if ($this->properties[$key] instanceof Type\Key)
		{
			if (isset($this->updates[$key]))
			{
				if ($this->updates[$key] instanceof \google\appengine\datastore\v4\Key)
				{
					$fkey = $this->values[$key];
				}
			}
			
			if (!isset($fkey) && isset($this->values[$key]) && $this->values[$key] instanceof \google\appengine\datastore\v4\Key)
			{
				$fkey = $this->values[$key]->rawValue();
			}
			
			if (!isset($fkey))
			{
				return null;
			}
			
			if (!isset($this->foreign[$key]))
			{
				$kindName = $fkey->getPathElement(0)->getKind();
				$className = str_replace('_', '\\', $kindName);
				
				$this->foreign[$key] = (new $className)
						->where('id', '==', $fkey)
					->first();
			}
			
			return $this->foreign[$key];
		}
		
		else if (isset($this->updates[$key]))
		{
			return $this->updates[$key];
		}
		
		if (isset($this->values[$key]))
		{
			return $this->values[$key]->rawValue();
		}
		
		if (isset($this->properties[$key]))
		{
			return null;
		}
	}
	
	public function __set($key, $val)
	{
		if ($key == 'id' && $val instanceof \google\appengine\datastore\v4\Key)
		{
			return $this->__key = $val;
		}
		else if ($val instanceof \google\appengine\datastore\v4\Key)
		{
			return $this->updates[$key] = $val;
		}
		else if ($val instanceof Model)
		{
			$this->updates[$key] = $val->key;
			return $this->foreign[$key] = $val;
		}
		
		if (!isset($this->properties[$key]))
		{
			throw new \Exception("Unknown Property for ".get_class($this).": ".$key);
		}
		
		return $this->updates[$key] = $val;
	}
	
	public function __isset($key)
	{
		return isset($this->values[$key]) || isset($this->updates[$key]);
	}
	
	public function toArray()
	{
		$ret = [];
		
		
		if (isset($this->__key))
		{
			$ret['id'] = $this->__key->getPathElement(0)->getId();
		}
		
		foreach ($this->properties as $key => $prop)
		{
			if (isset($this->updates[$key]))
			{
				$ret[$key] = $this->updates[$key];
			}
			else if (isset($this->values[$key]))
			{
				if (isset($this->values[$key]))
				{
					$ret[$key] = $this->values[$key]->rawValue();
				}
				else
				{
					$ret[$key] = $this->values[$key];
				}
			}
		}
		
		return $ret;
	}
	
	final public function __construct($entity = null)
	{
		parent::__construct();
		
		if ($entity)
		{
			$this->__key = $entity->entity->getKey();
			foreach($entity->entity->getPropertyList() as $property)
			{
				$this->values[$property->getName()] =
					new DataValue($property->getValue());
			}
		}
		
		foreach ($this->properties as $key => $property)
		{
			if (is_numeric($property))
			{
				$this->properties[$key] = Type::getTypeFromEnum($property);
			}
		}
		
		if (method_exists($this, 'define'))
		{
			$this->define();
		}
	}
}
