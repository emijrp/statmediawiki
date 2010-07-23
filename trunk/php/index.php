<?php

include("dependences/pChart/pChart/pData.class");   
include("dependences/pChart/pChart/pChart.class"); 

require_once("php/functions.php");

$type = "general";
if (isset($_GET["type"]))
{
    if ($_GET["type"]=="users") { $type = "users"; }
    if ($_GET["type"]=="pages") { $type = "pages"; }
}

if ($type == "users") { if (!existsUser($user)) { die("Ese usuario no existe"); } }
if ($type == "pages") { if (!existsPage($page)) { die("Esa página no existe"); } }

switch ($type)
{
    case "general":
        $filename = "csv/general/general.csv";
        break;
    case "pages":
        $filename = "csv/pages/page_".$page."_general.csv";
        break;
    case "users":
        $filename = "csv/users/user_".$user."_general.csv";
        break;
}
$f = fopen($filename, "r");
$raw = fread($f, filesize($filename));
$lines = split("[\n\r]", $raw);
$header = split(",", $lines[0]);
$values = split(",", $lines[1]);
fclose($f);
$general = array();
if (sizeof($header)!=sizeof($values))
{
    die ("Error en los datos generales");
}else{
    for ($i=0;$i<sizeof($header);$i++)
    {
        $general[$header[$i]] = $values[$i];
    }
}

printHeader($general["sitename"]);

echo "<dl>";
echo "<dt>Site:</dt>";
echo "<dd><a href='".$general["siteurl"]."'>".$general["sitename"]."</a></dd>";
echo "<dt>Generated:</dt>";
echo "<dd>...</dt>";
echo "<dt>Report period:</dt>";
echo "<dd>... &ndash; ...</dd>";
echo "<dt>Total pages:</dt>";
echo "<dd>".$general["totalpages"]." (Articles: ".$general["totalarticles"].")</dd>";
echo "<dt>Total edits:</dt>";
echo "<dd>".$general["totaledits"]." (In articles: ".$general["totaleditsinarticles"].")</dd>";
echo "<dt>Total bytes:</dt>";
echo "<dd>".$general["totalbytes"]." (In articles: ".$general["totalbytesinarticles"].")</dd>";
echo "<dt>Total files:</dt>";
echo '<dd><a href="http://osl.uca.es/">'.$general["totalfiles"].'</a></dd>';
echo "<dt>Users:</dt>";
echo "<dd><a href=''>".$general["totalusers"]."</a></dd>";

switch ($type)
{
    case "general":
        echo '<h2>Content evolution</h2>';
        echo '<h2>General activity</h2>';
        echo '<center>';
		echo '<table>
				  <tr>
					  <td><img src="php/generators/activity.php?type='.$type.'&time=hour" alt="Edits by hour" description="Edits by hour"/></td>
					  <td class="description"><p>MediaWiki almacena la fecha en la que se realiza cada edición en UTC, por lo que deberá sumar o restar el desplazamiento respecto a su zona horaria.</p><p>Si los usuarios del wiki provienen de una misma zona horaria, debería observar un patrón característico en la gráfica, cuyas horas más activas serían las diurnas.</p><div class="download-link">Download: [<a href="php/generators/activity.php?type='.$type.'&time=hour">PNG</a>] [<a href="csv/'.$type.'/general_hour_activity.csv">CSV</a>]</div></td>
				  </tr>
				  <tr>
					  <td><img src="php/generators/activity.php?type='.$type.'&time=dayofweek" alt="Edits by day of week" description="Edits by day of week"/></td>
					  <td class="description">aaa<div class="download-link">Download: [<a href="php/generators/activity.php?type='.$type.'&time=dayofweek">PNG</a>] [<a href="csv/'.$type.'/general_dayofweek_activity.csv">CSV</a>]</div><br/></td>
				  </tr>
				  <tr>
					  <td><img src="php/generators/activity.php?type='.$type.'&time=month" alt="Edits by month" description="Edits by month"/></td><td class="description">bbbbb<div class="download-link">Download: [<a href="php/generators/activity.php?type='.$type.'&time=month">PNG</a>] [<a href="csv/'.$type.'/general_month_activity.csv">CSV</a>]</div><br/></td>
				  </tr>
			 </table>';
        echo '</center>';
        
        echo '<h2>Users</h2>';
        echo '<h2>Pages</h2>';
        echo '<h2>Tags cloud</h2>';
        printHTMLCloud($type=$type);
        echo '<p class="download-link">[<a href="csv/'.$type.'/general_cloud.csv">Download as CSV</a>]</p>';
        break;
    case "users":
        echo '<img src="php/generators/hour_activity.php?type='.$type.'&time=dayofweek" alt="Edits by day of week" description="Edits by day of week"/>';
        break;
    case "users":
        echo '<img src="php/generators/hour_activity.php?type='.$type.'&time=month" alt="Edits by month" description="Edits by month"/>';
        break;
}



printFooter();

?>
