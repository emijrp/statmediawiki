<?php  

$user=False;
$page=False;
if (isset($_GET["user"])) { $user=$_GET["user"]; }
if (isset($_GET["page"])) { $page=$_GET["page"]; }

// Standard inclusions     
include("../../dependences/pChart/pChart/pData.class");  
include("../../dependences/pChart/pChart/pChart.class");  

// Dataset definition   
$DataSet = new pData;
$type = "general";
if (isset($_GET["type"]))
{
    if ($_GET["type"]=="pages") { $type = "pages"; }
    if ($_GET["type"]=="users") { $type = "users"; }
}
$time = "hour";
if (isset($_GET["time"]))
{
    if ($_GET["time"]=="dayofweek") { $time = "dayofweek"; }
    if ($_GET["time"]=="month") { $time = "month"; }
}

switch ($type)
{
    case "general":
        $filename = "../../csv/general/general_".$time."_activity.csv";
        break;
    case "pages":
        if (isset($_GET["page"])) { $page = $_GET["page"]; } #comprobar si la pagina existe con una tabla o algo
        $filename = "../../csv/pages/page_".$page."_".$time."_activity.csv";
        break;
    case "users":
        if (isset($_GET["user"])) { $user = $_GET["user"]; } #comprobar si el usuario existe con una tabla o algo, o si existe el fichero...
        $filename = "../../csv/users/user_".$user."_".$time."_activity.csv";
        break;
}

$DataSet->ImportFromCSV($filename,",",range(1,2),TRUE,0);  
$DataSet->AddAllSeries();
$DataSet->RemoveSerie("Serie0");
$DataSet->SetAbsciseLabelSerie();  
$DataSet->SetYAxisName("Edits");
switch ($time)
{
    case "hour":
        $DataSet->SetXAxisName("Hours");  
        break;
    case "dayofweek":
        $DataSet->SetXAxisName("Days of week");  
        break;
    case "month":
        $DataSet->SetXAxisName("Months");  
        break;
}

// Initialise the graph  
$Test = new pChart(700,230);  
$Test->reportWarnings("GD");
$Test->drawGraphAreaGradient(132,173,131,50,TARGET_BACKGROUND);  
$Test->setFontProperties("../../dependences/pChart/Fonts/tahoma.ttf",8);  
$Test->setGraphArea(120,20,675,190);  
$Test->drawGraphArea(213,217,221,FALSE);  
$Test->drawScale($DataSet->GetData(),$DataSet->GetDataDescription(),SCALE_ADDALL,213,217,221,TRUE,0,2,TRUE);  
$Test->drawGraphAreaGradient(163,203,167,50);  
$Test->drawGrid(4,TRUE,230,230,230,20);  

// Draw the bar chart  
$Test->drawStackedBarGraph($DataSet->GetData(),$DataSet->GetDataDescription(),70);  

// Draw the title  
switch ($time)
{
    case "hour":
        $Title = "  Edits per hour\r\n  ";
        break;
    case "dayofweek":
        $Title = "  Edits per day of week\r\n  ";
        break;
    case "month":
        $Title = "  Edits per month\r\n  ";
        break;
}
$Test->drawTextBox(0,0,50,230,$Title,90,255,255,255,ALIGN_BOTTOM_CENTER,TRUE,0,0,0,30);  

// Draw the legend  
$Test->setFontProperties("../../dependences/pChart/Fonts/tahoma.ttf",8);  
$Test->drawLegend(600,10,$DataSet->GetDataDescription(),236,238,240,52,58,82);  

// Render the picture  
$Test->addBorder(1);  
$Test->Stroke();  
?>
