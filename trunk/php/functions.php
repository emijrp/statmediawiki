<?php

function printHeader($title = "")
{
	$output = '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">';
	$output .= '<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="es" lang="es" dir="ltr">';
	$output .= '<header>';
	$output .= '<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />';
	$output .= '<link rel="stylesheet" href="php/styles/style.css" type="text/css" media="all" />';
	$output .= '<title>StatMediaWiki: '.$title.'</title>';
	$output .= '</header>';
	$output .= '<body>';
	$output .= '<h1>StatMediaWiki: '.$title.'</h1>';
	
	print $output;
}

function printFooter()
{
	$output = '<hr/><center>Generated with <a href="http://statmediawiki.forja.rediris.es/">StatMediaWiki</a></center>';
	$output .= '</body>';
	$output .= '</html>';
	
	echo $output;
}

?>
