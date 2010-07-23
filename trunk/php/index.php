<?php

include("dependences/pChart/pChart/pData.class");   
include("dependences/pChart/pChart/pChart.class"); 

require_once("php/functions.php");

printHeader();

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
print $raw;
fclose($f);

switch ($type)
{
    case "general":
        echo '<center>';
        echo '<h2>General activity</h2>';
        echo '<img src="php/generators/activity.php?type='.$type.'&time=hour" alt="Edits by hour" description="Edits by hour"/><br/><p class="download-link">[<a href="php/generators/activity.php?type='.$type.'&time=hour">Download as PNG</a>] [<a href="csv/'.$type.'/general_hour_activity.csv">Download CSV</a>]</p><br/>';
        echo '<img src="php/generators/activity.php?type='.$type.'&time=dayofweek" alt="Edits by day of week" description="Edits by day of week"/><br/><p class="download-link">[<a href="php/generators/activity.php?type='.$type.'&time=dayofweek">Download as PNG</a>] [<a href="csv/'.$type.'/general_dayofweek_activity.csv">Download as CSV</a>]</p><br/>';
        echo '<img src="php/generators/activity.php?type='.$type.'&time=month" alt="Edits by month" description="Edits by month"/><br/><p class="download-link">[<a href="php/generators/activity.php?type='.$type.'&time=month">Download as PNG</a>] [<a href="csv/'.$type.'/general_month_activity.csv">Download as CSV</a>]</p><br/>';
        echo '</center>';
        break;
    case "users":
        echo '<img src="php/generators/hour_activity.php?type='.$type.'&time=dayofweek" alt="Edits by day of week" description="Edits by day of week"/>';
        break;
    case "users":
        echo '<img src="php/generators/hour_activity.php?type='.$type.'&time=month" alt="Edits by month" description="Edits by month"/>';
        break;
}
/*
echo "<dl>";
echo "<dt>Site:</dt>";
echo "<dd><a href='http://osl.uca.es/wikira'>WikiRA</a></dd>";
echo "<dt>Generated:</dt>";
echo "<dd>2010-06-29T10:43:29.034021</dt>";
echo "<dt>Report period:</dt>";
echo "<dd>2010-02-15T00:00:00 - 2010-06-30T00:00:00</dd>";
echo "<dt>Total pages:</dt>";
echo "<dd>89 (Articles: 27)</dd>";
echo "<dt>Total edits:</dt>";
echo "<dd>473 (In articles: 345)</dd>";
echo "<dt>Total bytes:</dt>";
echo "<dd>247649 (In articles: 234075)</dd>";
echo "<dt>Total files:</dt>";
#echo "<dd><a href="http://osl.uca.es/wikira/index.php/Special:Imagelist">39</a></dd>";
echo "<dt>Users:</dt>";
#echo "<dd><a href="users.php">67</a></dd>";
*/

echo "<h2>Users</h2>";
echo "<h2>Pages</h2>";
echo "<h2>Tags cloud</h2>";

printFooter();

?>
