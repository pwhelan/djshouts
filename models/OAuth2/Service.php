<?php

namespace Djshouts\OAuth2;

use Datachore\Type;


class Service extends \Datachore\Model
{
	protected $properties = [
		'name'			=> Type::String,
		'connect_url'		=> Type::String,
		'access_token_url'	=> Type::String,
		'client_id'		=> Type::String,
		'client_secret'		=> Type::String,
		'connectbutton'		=> Type::String,
		'is_post'		=> Type::Boolean
	];
	
	public function get_connect_url()
	{
		$url = parse_url($this->connect_url);
		$query = []; parse_str($url['query'], $query);
		
		$query['client_id'] = $this->client_id;
		$query['redirect_uri'] = ($_SERVER['HTTPS'] == 'on' ? 'https://' : 'http://')
			. $_SERVER['HTTP_HOST'] . '/oauth2/callback/' . $this->name;
		
		return
			$url['scheme'] .'://' .
			$url['host'] .
			$url['path'] . '?' .
			http_build_query($query);
	}
}
