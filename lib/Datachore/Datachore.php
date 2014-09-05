<?php

namespace Datachore;

class Datachore implements \Iterator
{
	private $_datasetId = null;
	private $_datastore = null;
	private $__results = null;
	private $__resIndex = -1;
	private $__entities = [];
	private $__result = null;
	private $__changed = [];
	private $__id = 0;
	
	
	public function setDatastore(Datastore $datastore)
	{
		$this->_datastore = $datastore;
		$this->setDatasetId($datastore->getDatasetId());
	}
	
	public function setDatasetId($datasetId)
	{
		$this->_datasetId = $datasetId;
	}
	
	public function datasetId()
	{
		return $this->_datasetId;
	}
	
	private function _kind_from_class($className = NULL)
	{
		if (!$className) {
			$className = get_class($this);
		}
		
		return strtolower(str_replace('\\', '_', $className));
	}
	
	public function rewind()
	{
		$this->__resIndex = 0;
	}
	
	public function __get($key)
	{
		if ($key == 'id' && $this->__id) {
			return $this->__id;
		}
		else if ($this->__result && isset($this->__changed[$key])) {
			return $this->__changed[$key];
		}
		
		$props = $this->__result->getPropertyList();
		foreach ($props as $prop)
		{
			if ($prop->getName() == $key)
			{
				return new DataValue($prop->getValue());
			}
		}
		
		throw new \Exception('Non existent property: '.$key);
	}
	
	public function __isset($key)
	{
		if ($key == 'id') return $this->__id != 0;
		else if ($this->__result && isset($this->__changed[$key])) return true;
		
		$props = $this->__result->getPropertyList();
		foreach ($props as $prop)
		{
			if ($prop->getName() == $key)
			{
				return true;
			}
		}
		return false;
	}
	
	public function __set($key, $val)
	{
		if ($key == 'id') {
			throw new \Exception('Entity ID is read only');
		}
		$this->__changed[$key] = $val;
	}
	
	public function loadFromEntity($obj)
	{
		$this->__result = $obj->entity;
		$this->__id = $obj->entity->getKey()->getPathElement(0)->getId();
	}
	
	public function current()
	{
		try {
			$resEntity = $this->__results->batch->getEntityResult($this->__resIndex);
		}
		catch (\OutOfRangeException $range) {
			return;
		}
		$className = get_class($this);
		
		$entity = new $className;
		$entity->loadFromEntity($resEntity);
		
		$this->__entities[$this->__resIndex] = $entity;
		return $this->__entities[$this->__resIndex];
	}
	
	public function key()
	{
		return $this->__resIndex;
	}
	
	public function next()
	{
		$this->__resIndex++;
	}
	
	public function valid()
	{
		return $this->__resIndex < $this->__results->batch->getEntityResultSize();
	}
	
	public function datastore()
	{
		if ($this->_datastore == null)
		{
			$this->setDatastore(Datastore::getInstance());
		}
		
		return $this->_datastore;
	}
	
	public function save()
	{
		$transactionRequest = $this->datastore()->Factory('BeginTransactionRequest');
		//$isolationLevel->setIsolationLevel('snapshot');
		
		$transaction = $this->datastore()->beginTransaction(
			$this->datasetId(),
			$transactionRequest
		);
		
		$commit = $this->datastore()->Factory('CommitRequest');
		
		
		if ($this->__result) {
			$newkeys = array_diff(
				array_keys($this->__changed),
				array_keys($this->__result['entity']['properties'])
			);
			
			foreach($this->__result['entity']['properties'] as $k => $v) {
				$property = self::$_datastore->Factory('Property');
				
				if (isset($this->__changed[$k])) {
					$property->setStringValue($this->__changed[$k]);
				}
				else {
					$property->setStringValue($v['stringValue']);
				}
				
				$properties[$k] = $property;
			}
		}
		else {
			foreach($this->__changed as $key => $value)
			{
				$property = self::$_datastore->Factory('Property');
				$property->setStringValue($value);
				$properties[$key] = $property;
			}
		}
		
		
		if ($this->__result) $key = $this->_GoogleKeyValue($this->id);
		else $key = $this->_GoogleKeyValue();
		
		$entity->setKey($key);
		$entity->setProperties($properties);
		
		if ($this->__result) $mutation->setUpdate([$entity]);
		else $mutation->setInsertAutoId([$entity]);
		
		$commit->setMutation($mutation);
		$commit->setTransaction($transaction['transaction']);
		
		
		$rc = self::$_dataset->commit(self::$_datasetId, $commit);
		if (!$this->__result) {
			$this->__id = $rc['mutationResult']['insertAutoIdKeys'][0]['path'][0]['id'];
		}
		
		$this->__changed = [];
		return $rc;
	}
	
	const WHERE_EQ		= 1;
	const WHERE_LT 		= 2;
	const WHERE_LTEQ	= 3;
	const WHERE_GT		= 4;
	const WHERE_GTEQ	= 5;
	
	private $__filters = null;
	
	
	private $_operator_strings = [
		self::WHERE_EQ		=> 'equal',
		self::WHERE_LT		=> 'lessThan',
		self::WHERE_LTEQ	=> 'lessThanOrEqual',
		self::WHERE_GT		=> 'greaterThan',
		self::WHERE_GTEQ	=> 'greaterThanOrEqual'
	];
	
	
	final protected function _GoogleKeyValue($id = null)
	{
		$key = self::$_datastore->Factory('Key');
		$partitionId = self::$_datastore->Factory('PartitionId');
		$path = self::$_datastore->Factory('Key\PathElement');
		
		$partitionId->setDatasetId(self::$_datasetId);
		
		if($id) $path->setId($id);
		$path->setKind($this->_kind_from_class());
		
		$key->setPartitionId($partitionId);
		$key->setPath([$path]);
		
		
		return $key;
	}
	
	private function _where($propertyName, $operatorEnum, $rawValue)
	{
		$filter = self::$_datastore->Factory('PropertyFilter');
		$value = self::$_datastore->Factory('Value');
		if ($propertyName == 'id') {
			$value->setKeyValue($this->_GoogleKeyValue($rawValue));
		}
		else {
			$value->setStringValue($rawValue);
		}
		
		$propRef = self::$_datastore->Factory('PropertyReference');
		
		if ($propertyName == 'id') $propRef->setName('__key__');
		else $propRef->setName($propertyName);
		
		$filter->setProperty($propRef);
		$filter->setOperator($this->_operator_strings[$operatorEnum]);
		$filter->setValue($value);
		
		$this->__filters->add($filter);
	}
	
	public static function all()
	{
		$_class = get_called_class();
		$instance = new $_class;
		return $instance->get();
	}
	
	public function get()
	{
		//$query = self::$_datastore->Factory('Query');
		$request = self::$_datastore->Factory('RunQueryRequest');
		$query = $request->mutableQuery();
		
		
		if ($this->__filters)
		{
			$filters = $this->__filters->get();
			if (self::$_datastore->isInstanceOf($filters, 'CompositeFilter'))
			{
				$filter = self::$_datastore->Factory('Filter');
				$filter->setCompositeFilter($filters);
			}
			
			if (self::$_datastore->isInstanceOf($filters, 'Filter'))
			{
				$filter = $filters;
				$query->setFilter($filter);
			}
		}
		
		$kind = $query->addKind();
		$kind->setName($this->_kind_from_class());
		
		$partition_id = $request->mutablePartitionId();
		$partition_id->setDatasetId(self::$_datasetId);
		
		$this->__results = self::$_dataset->runQuery(self::$_datasetId, $request);
		$this->rewind();
		
		return $this;
	}
	
	public function __call($func, $args)
	{
		$ifunc = strtolower($func);
		
		
		if (substr($ifunc, 0, 5) == 'where' || substr($ifunc, 0, 7) == 'orwhere' || substr($ifunc, 0, 8) == 'andwhere') {
			
			if (substr($ifunc, 0, 7) == 'orwhere') {
				$operator = 'or';
			}
			else {
				$operator = 'and';
			}
			
			if (substr($ifunc, 0, strlen($operator)) == $operator) {
				$ifunc = substr($ifunc, strlen($operator));
			}
			
			if ($this->__filters == null) {
				$this->__filters = new FilterStack($operator);
			}
			
			if ($ifunc == 'where') {
				
				if (count($args) == 1 && $args[0] instanceof \Closure) {
					
					$filters = $this->__filters;
					
					$this->__filters = new FilterStack($operator);
					$args[0]($this);
					
					$filters->add($this->__filters);
					$this->__filters = $filters;
					
					return $this;
				}
				
				if (count($args) != 3) {
					throw new \Exception('Insufficient arguments for WHERE clause');
				}
				
				list($property, $operator, $value) = $args;
				
				
				if (is_string($operator)) {
					switch($operator) {
					case '=':
					case '==':
						$operator = self::WHERE_EQ;
						break;
					case '<':
						$operator = self::WHERE_LT;
						break;
					case '<=':
						$operator = self::WHERE_LTEQ;
						break;
					case '>':
						$operator = self::WHERE_GT;
						break;
					case '>=':
						$operator = self::WHERE_GTEQ;
						break;
					}
				}
			}
			else {
				if (count($args) != 2) {
					throw new \Exception('Insufficient arguments for WHERE clause');
				}
				
				$opstr = substr($ifunc, 5);
				
				switch(strtolower($opstr)) {
				case 'eq':
				case 'equals':
					$operator = self::WHERE_EQ;
					break;
				case 'lt':
				case 'lessthan':
					$operator = self::WHERE_LT;
					break;
				case 'lteq':
				case 'lessthanequal':
				case 'lessthanequals':
				case 'lessthanorequal':
				case 'lessthanorequals':
					$operator = self::WHERE_LTEQ;
					break;
				case 'gt':
				case 'greaterthan':
					$operator = self::WHERE_GT;
					break;
				case 'gteq':
				case 'greaterthanequal':
				case 'greaterthanequals':
				case 'greaterthanorequal':
				case 'greaterhanorequals':
					$operator = self::WHERE_GTEQ;
					break;
				default:
					throw new Exception('Unknown Operator');
				}
				
				list($property, $value) = $args;
			}
			
			$this->_where($property, $operator, $value);
			return $this;
		}
		
		throw new \Exception("No such method");
	}
	
	public static function __callStatic($func, $args)
	{
		$ifunc = strtolower($func);
		if (substr($ifunc, 0, 5) == 'where' || substr($ifunc, 0, 7) == 'orwhere' || substr($ifunc, 0, 8) == 'andwhere') {
			$_class = get_called_class();
			$instance = new $_class;
			
			return call_user_func_array([$instance, $func], $args);
		}
		
		throw new \Exception("No such static method");
	}
}
