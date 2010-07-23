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

function printHTMLCloud($type="general", $limit=50)
{
    $minSize = 100;
    $maxSize = 300;
    
    $filename = "csv/".$type."/general_cloud.csv";
    $f = fopen($filename, "r");
    $raw = fread($f, filesize($filename));
    fclose($f);
    
    $lines = split("[\r\n]", $raw);
    array_shift($lines); #quitamos header
    if (sizeof($lines)<$limit) { $limit = sizeof($lines); }
    $lines = array_slice($lines, $limit); #nos quedamos con las $limit primeras
    
    shuffle($lines);
    
    $tags = array();
    $maxTimes = 0;
    $minTimes = 999999;
    for ($i=1;$i<=$limit;$i++) #nos saltamos la 0 que contiene el header
    {
        $line = split(",", $lines[$i]);
        $tag = $line[0];
        $times = $line[1];
        
        $tags[$tag] = $times;
        if ($maxTimes<$times) { $maxTimes = $times; }
        if ($minTimes>$times) { $minTimes = $times; }
    }
    
    $output = "";
    foreach ($tags as $tag=>$times)
    {
        $fontSize = (($times - $minTimes) * ($maxSize - $minSize)) / ($maxTimes - $minTimes);
        $output .= '<span style="font-size: '.$fontSize.'%">'.$tag.'</span> &nbsp;&nbsp;&nbsp;';
    }
    
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
