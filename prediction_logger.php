<?php

$MAX_RETRIES = 3;
$retry = 0;

$session = curl_init();
curl_setopt($session, CURLOPT_RETURNTRANSFER, true);
curl_setopt($session, CURLOPT_FOLLOWLOCATION, true);
curl_setopt($session, CURLOPT_URL, 'https://spzroenkhausen.bplaced.net/api/v0/events.php?api_token=0eef5dacbf418992610dbf2bf593f57c');

while($retry < $MAX_RETRIES){
    $contents = curl_exec($session);

    if($contents == false){
        $retry++;
    } else {
        break;
    }
}

curl_close($session);

if($contents == false){
    echo "Failed to fetch events\n";
    exit(1);
}

$events = json_decode($contents);

date_default_timezone_set('Europe/Berlin');

if($events){
    foreach($events as $event){
        # skip events that are already over or too far in the future
        if($event->Date < date("Y-m-d") || $event->Date > date("Y-m-d", strtotime("+60 days"))){
            continue;
        }

        if($event->Date == date("Y-m-d")){
            if($event->Begin < date("H:i")){
                continue;
            }
        }

        $ev_attendence = json_decode(file_get_contents('https://spzroenkhausen.bplaced.net/api/v0/attendence/' . $event->Event_ID . '?api_token=0eef5dacbf418992610dbf2bf593f57c'));
        $ev = json_decode(file_get_contents('https://spzroenkhausen.bplaced.net/api/v0/events/' . $event->Event_ID . '?api_token=0eef5dacbf418992610dbf2bf593f57c'));

        $prediction = $ev_attendence->Attendence->Consent + $ev_attendence->Attendence->ProbAttending + $ev_attendence->Attendence->PlusOne;
        $consent = $ev_attendence->Attendence->Consent + $ev_attendence->Attendence->PlusOne;
        $maybe = $ev_attendence->Attendence->Maybe;

        $logentry = date("Y-m-d H:i") . ", " . $prediction . ", " . $consent . ", " . $maybe;

        if($ev->Category == "event"){

            if($ev->Date <= date("Y-m-d", strtotime("+1 week"))){
                // get location
                if($ev->Address == ""){
                    $ev->Address = $ev->Location;
                }
                
                // get geo coordinates
                $url = "https://api.maptiler.com/geocoding/";
                $add = urlencode($ev->Address);
                $url .= $add;
                $url .= ".json?key=m4hEVQNm2k3vfyEB1Bsy";

                $session = curl_init();
                curl_setopt($session, CURLOPT_RETURNTRANSFER, true);
                curl_setopt($session, CURLOPT_FOLLOWLOCATION, true);
                curl_setopt($session, CURLOPT_URL, $url);

                $contents = curl_exec($session);

                curl_close($session);

                $geo = json_decode($contents);

                $lat = $geo->features[0]->geometry->coordinates[1];
                $lon = $geo->features[0]->geometry->coordinates[0];

                // get weather
                $url = "https://api.open-meteo.com/v1/forecast?latitude=" . $lat . "&longitude=" . $lon . "&hourly=apparent_temperature,weathercode&start_date=" . $ev->Date . "&end_date=" . $ev->Date . "&timezone=Europe/Berlin";

                $session = curl_init();
                curl_setopt($session, CURLOPT_RETURNTRANSFER, true);
                curl_setopt($session, CURLOPT_FOLLOWLOCATION, true);
                curl_setopt($session, CURLOPT_URL, $url);

                $contents = curl_exec($session);

                curl_close($session);

                $weather = json_decode($contents);

                // get weather for event time
                $hour = substr($ev->Begin, 0, 2);
                $hour = intval($hour);

                $weathercode = $weather->hourly->weathercode[$hour];
                $temperature = $weather->hourly->apparent_temperature[$hour];
            } else {
                $weathercode = "-1";
                $temperature = "-1";
            }

            $logentry .= ", " . $weathercode . ", " . $temperature . "\n";
        } else {
            $logentry .= "\n";
        }


        if(is_dir(dirname(__FILE__) . "/prediction_log/") == false){
            mkdir(dirname(__FILE__) . "/prediction_log/");
        }

        $filename = $event->Event_ID . "-" . $event->Type . ".csv";

        // remove german special characters from filename
        $filename = str_replace(array('ä', 'ö', 'ü', 'ß', 'Ä', 'Ö', 'Ü'), array('ae', 'oe', 'ue', 'ss', 'Ae', 'Oe', 'Ue'), $filename);

        // remove special characters from filename
        $filename = preg_replace('/[^A-Za-z0-9\-\.]/', '_', $filename);

        $filename = dirname(__FILE__) . "/prediction_log/" . $filename;

        if (!file_exists($filename)){
            $logfile = fopen($filename, "a");
            if($ev->Category == "event"){
                fwrite($logfile, "Date, Prediction, Consent, Maybe, Weathercode, Temperature\n");
            } else {
                fwrite($logfile, "Date, Prediction, Consent, Maybe\n");
            }
        } else {
            $logfile = fopen($filename, "a");
        }

        fwrite($logfile, $logentry);
        fclose($logfile);
    }
}

?>