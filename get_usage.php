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
$minor_versions = array();

foreach($versions as $version){
    foreach($version as $v => $count){
        array_push($all_versions, $v);
        // strip x.x.x to x.x
        $v_exp = explode(".", $v);
        $v_minor = $v_exp[0] . "." . $v_exp[1];
        array_push($minor_versions, $v_minor);
    }
}

$all_versions = array_unique($all_versions);
$minor_versions = array_unique($minor_versions);

usort($all_versions, function($a, $b){
    $a_vers = substr($a, 1);
    $b_vers = substr($b, 1);
    return version_compare($a_vers, $b_vers);
});

usort($minor_versions, function($a, $b){
    $a_vers = substr($a, 1);
    $b_vers = substr($b, 1);
    return version_compare($a_vers, $b_vers);
});

$version_file = fopen(dirname(__FILE__) . "/usage_log/versions.csv", "w");
$minorversion_file = fopen(dirname(__FILE__) . "/usage_log/minor_versions.csv", "w");
fwrite($version_file, "Date");
fwrite($minorversion_file, "Date");

foreach($all_versions as $v){
    fwrite($version_file, ", " . $v);
}

foreach($minor_versions as $v){
    fwrite($minorversion_file, ", " . $v);
}

fwrite($version_file, "\n");
fwrite($minorversion_file, "\n");

for ($i = $interval; $i > 0; $i--){
    $date = date("Y-m-d", strtotime($today . " - " . $i . " days"));
    $version = $versions[$interval - $i];

    fwrite($version_file, $date);
    fwrite($minorversion_file, $date);

    foreach($all_versions as $v){
        if(isset($version->$v)){
            fwrite($version_file, ", " . $version->$v);
        } else {
            fwrite($version_file, ", 0");
        }
    }

    foreach($minor_versions as $v){
        $c = 0;

        foreach($version as $v2 => $count){
            $v_exp = explode(".", $v2);
            $v_minor = $v_exp[0] . "." . $v_exp[1];
            if($v_minor == $v)
                $c += $count;
        }
        
        fwrite($minorversion_file, ", " . $c);
    }
            

    fwrite($version_file, "\n");
    fwrite($minorversion_file, "\n");
}

fclose($version_file);
fclose($minorversion_file);
?>