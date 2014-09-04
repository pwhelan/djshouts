<?php

namespace Datachore;

class FilterStack
{
	private $__filters = [];
	private $__operator;
	
	
	public function __construct($operator = 'and')
	{
		$this->__operator = $operator;
	}
	
	public function add($filter)
	{
		if ($filter instanceof \Google_Service_Datastore_PropertyFilter) {
			$this->__filters[] = $filter;
		}
		else if ($filter instanceof DatachoreFilterStack) {
			$this->__filters[] = $filter->get();
		}
	}
	
	public function get()
	{
		if (count($this->__filters) == 0) {
			return [];
		}
		else if (count($this->__filters) == 1) {
			$propertyFilter = array_shift($this->__filters);
			
			$filter = new \Google_Service_Datastore_Filter;
			if ($propertyFilter instanceof \Google_Service_Datastore_PropertyFilter) {
				$filter->setPropertyFilter($propertyFilter);
			}
			else if ($propertyFilter instanceof \Google_Service_Datastore_CompositeFilter) {
				$filter->setCompositeFilter($propertyFilter);
			}
			
			return $filter;
		}
		else if (count($this->__filters) > 1) {
			
			$filter = new \Google_Service_Datastore_CompositeFilter;
			$filter->setFilters(
				array_map(function($prop) {
						$filter = new \Google_Service_Datastore_Filter;
						$filter->setPropertyFilter($prop);
						return $filter;
					},
					$this->__filters
				));
			$filter->setOperator($this->__operator);
			
			return $filter;
		}
	}
}
