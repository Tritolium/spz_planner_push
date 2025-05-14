<?php
$events = json_decode(file_get_contents('https://spzroenkhausen.bplaced.net/api/v0/events?api_token=0eef5dacbf418992610dbf2bf593f57c'));

$delta_events = [2,4,6];
$delta_practices = [1,2,6,8,10];
$delta = [];

// filter out events that are not today or already declined
if($events){
    foreach($events as $event){
        if($event->Date != date("Y-m-d") || $event->State > 1){
            unset($events[array_search($event, $events)]);
        }
    }
}

if($events == NULL){
    echo "No events today\n";
    exit(1);
}

if($events){
    foreach($events as $event){
        if($event->Departure != NULL){
            $runtime_h = substr($event->Departure, 0, 2);
            $runtime_m = substr($event->Departure, 2, 3);
        } else {
            $runtime_h = substr($event->Begin, 0, 5);
            $runtime_m = substr($event->Begin, 2, 3);
        }

        switch($event->Category) {
            default:
            case "other":
            case "event":
                $delta = $delta_events;
                break;
            case "practice":
                $delta = $delta_practices;
                break;            
        }

        for ($i = 0; $i < count($delta); $i++){
            $runtime_h_d = intval($runtime_h) - $delta[$i];
            if ($runtime_h_d <= 0) {
                continue;
            }

            if ($i == 0) {
                exec("at " . $runtime_h_d . $runtime_m . " <<EOT\n php " . dirname(__FILE__) . "/send_push.php " . $event->Event_ID . " " . $event->Type . " \"" . $event->Location . "\" " . "monly" ." >> /home/pog/push_log/" . $event->Event_ID . ".log\nEOT");
            } else {
                exec("at " . $runtime_h_d . $runtime_m . " <<EOT\n php " . dirname(__FILE__) . "/send_push.php " . $event->Event_ID . " " . $event->Type . " \"" . $event->Location . "\" >> /home/pog/push_log/" . $event->Event_ID . ".log\nEOT");
            }
        }
    }
}
?>
