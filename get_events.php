<?php
$events = json_decode(file_get_contents('https://spzroenkhausen.bplaced.net/api/event.php?api_token=0eef5dacbf418992610dbf2bf593f57c&today'));

if($events){
    foreach($events as $event){
        if($event->Departure != NULL){
            $runtime_h = substr($event->Departure, 0, 2);
            $runtime_m = substr($event->Departure, 2, 3);
        } else {
            $runtime_h = substr($event->Begin, 0, 5);
            $runtime_m = substr($event->Begin, 2, 3);
        }
    
        $runtime_h_1 = intval($runtime_h) - 2;
        $runtime_h_2 = intval($runtime_h) - 1;
        if(!str_contains($event->Type, "Abgesagt")){
            exec("at " . $runtime_h_1 . $runtime_m . " <<EOT\n php " . dirname(__FILE__) . "/send_push.php " . $event->Event_ID . " " . $event->Type . " " . $event->Location . " >> /home/pog/push_log/" . $event->Event_ID . ".log\nEOT");
        exec("at " . $runtime_h_2 . $runtime_m . " <<EOT\n php " . dirname(__FILE__) . "/send_push.php " . $event->Event_ID . " " . $event->Type . " " . $event->Location . " >> /home/pog/push_log/" . $event->Event_ID . ".log\nEOT");
        }
    }
}
?>
