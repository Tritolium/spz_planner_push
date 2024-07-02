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

$versions = array();

for ($i = $interval; $i > 0; $i--){
    $date = date("Y-m-d", strtotime($today . " - " . $i . " days"));
    $stats = json_decode(file_get_contents('https://spzroenkhausen.bplaced.net/api/eval.php?api_token=0eef5dacbf418992610dbf2bf593f57c&statistics&date=' . $date));
    $usage = $stats->Users;

    fwrite($file, $date . ", " . $usage->Today->Daily . ", " . $usage->Today->Calls . ", " . $usage->Seven->Daily . ", " . $usage->Seven->Calls . ", " . $usage->Thirty->Daily . ", " . $usage->Thirty->Calls . "\n");

    array_push($versions, $stats->Versions);
}

fclose($file);

// get all included versions
$all_versions = array();

foreach($versions as $version){
    foreach($version as $v => $count){
        array_push($all_versions, $v);
    }
}

$all_versions = array_unique($all_versions);

usort($all_versions, function($a, $b){
    $a_vers = substr($a, 1);
    $b_vers = substr($b, 1);
    return version_compare($a_vers, $b_vers);
});

$version_file = fopen(dirname(__FILE__) . "/usage_log/versions.csv", "w");
fwrite($version_file, "Date");

foreach($all_versions as $v){
    fwrite($version_file, ", " . $v);
}

fwrite($version_file, "\n");

for ($i = $interval; $i > 0; $i--){
    $date = date("Y-m-d", strtotime($today . " - " . $i . " days"));
    $version = $versions[$interval - $i];

    fwrite($version_file, $date);

    foreach($all_versions as $v){
        if(isset($version->$v)){
            fwrite($version_file, ", " . $version->$v);
        } else {
            fwrite($version_file, ", 0");
        }
    }

    fwrite($version_file, "\n");
}

fclose($version_file);
?>