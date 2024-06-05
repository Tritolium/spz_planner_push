<?php
$events = json_decode(file_get_contents('https://spzroenkhausen.bplaced.net/api/v0/events.php?api_token=0eef5dacbf418992610dbf2bf593f57c'));

date_default_timezone_set('Europe/Berlin');

if($events){
    foreach($events as $event){
        # skip events that are already over or too far in the future
        if($event->Date < date("Y-m-d") || $event->Date > date("Y-m-d", strtotime("+3 days"))){
            continue;
        }

        if($event->Date == date("Y-m-d")){
            if($event->Begin < date("H:i")){
                continue;
            }
        }

        $ev_attendence = json_decode(file_get_contents('https://spzroenkhausen.bplaced.net/api/v0/attendence/' . $event->Event_ID . '?api_token=0eef5dacbf418992610dbf2bf593f57c'));

        $prediction = $ev_attendence->Attendence->Consent + $ev_attendence->Attendence->ProbAttending + $ev_attendence->Attendence->PlusOne;
        $consent = $ev_attendence->Attendence->Consent + $ev_attendence->Attendence->PlusOne;
        $maybe = $ev_attendence->Attendence->Maybe;

        $logentry = date("Y-m-d H:i") . ", " . $prediction . ", " . $consent . ", " . $maybe . "\n";

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
            fwrite($logfile, "Date, Prediction, Consent, Maybe\n");
        } else {
            $logfile = fopen($filename, "a");
        }

        fwrite($logfile, $logentry);
        fclose($logfile);
    }
}

?>