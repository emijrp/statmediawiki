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
$filename = "../../csv/general/general_hour_activity.csv";
if ($user)
{
	$filename="../../csv/users/user_".$user."_hour_activity.csv";
}else{
	if ($page)
	{
		$filename="../../csv/pages/page_".$page."_hour_activity.csv";
	}
}
$DataSet->ImportFromCSV($filename,",",range(1,2),TRUE,0);  
$DataSet->AddAllSeries();
$DataSet->RemoveSerie("Serie0");
$DataSet->SetAbsciseLabelSerie();  
$DataSet->SetYAxisName("Edits");  
$DataSet->SetXAxisName("Hours");  

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
$Title = "  Edits per hour\r\n  ";  
$Test->drawTextBox(0,0,50,230,$Title,90,255,255,255,ALIGN_BOTTOM_CENTER,TRUE,0,0,0,30);  

// Draw the legend  
$Test->setFontProperties("../../dependences/pChart/Fonts/tahoma.ttf",8);  
$Test->drawLegend(600,10,$DataSet->GetDataDescription(),236,238,240,52,58,82);  

// Render the picture  
$Test->addBorder(1);  
$Test->Stroke();  
?>
