<?php

if(!isset($argv[1])){
    echo "No interval given, using default interval of 1 day\n";
    $interval = 1;
} else {
    $interval = $argv[1];
}

if(is_dir(dirname(__FILE__) . "/usage_log/") == false){
    mkdir(dirname(__FILE__) . "/usage_log/");
}

$filename = dirname(__FILE__) . "/usage_log/usage.csv";

$file = fopen($filename, "w");
fwrite($file, "Date, Today, Calls, Week, W_Calls, Month, M_Calls\n");

$today = date("Y-m-d");

for ($i = $interval; $i > 0; $i--){
    $date = date("Y-m-d", strtotime($today . " - " . $i . " days"));
    $stats = json_decode(file_get_contents('https://spzroenkhausen.bplaced.net/api/eval.php?api_token=0eef5dacbf418992610dbf2bf593f57c&statistics&date=' . $date));
    $usage = $stats->Users;

    fwrite($file, $date . ", " . $usage->Today->Daily . ", " . $usage->Today->Calls . ", " . $usage->Seven->Daily . ", " . $usage->Seven->Calls . ", " . $usage->Thirty->Daily . ", " . $usage->Thirty->Calls . "\n");
}

?>