<?php

require __DIR__ . '/vendor/autoload.php';
require 'send_single_push.php';

// use Minishlink\Webpush\Webpush;

$url = 'https://spzroenkhausen.bplaced.net';

if(isset($argv[1]) == false){
	echo "No event_id given\n";
	exit();
}

if(isset($argv[2]) == false){
	echo "No event_type given\n";
	exit();
}

if(isset($argv[3]) == false){
	echo "No event_location given\n";
	exit();
}

if(isset($argv[4]) == false){
	$missing_only = false;
} else {
	if ($argv[4] == "monly") {
		$missing_only = true;
	} else {
		$missing_only = false;
	}
}

if($missing_only){
	$subscriptions = json_decode(file_get_contents($url . '/api/attendence.php?api_token=0eef5dacbf418992610dbf2bf593f57c&missing&monly&event_id=' . $argv[1]));
} else {
	$subscriptions = json_decode(file_get_contents($url . '/api/attendence.php?api_token=0eef5dacbf418992610dbf2bf593f57c&missing&event_id=' . $argv[1]));
}

if($subscriptions == null){
	send_single_push(0);
	exit();
}


$auth = [
	'VAPID' => [
		'subject' => 'https://tritolium.github.io',
		'publicKey' => 'BD0AbKmeW7bACNzC9m0XSUddJNx--VoOvU2X0qBF8dODOBhHvFPjrKJEBcL7Yk07l8VpePC1HBT7h2FRK3bS5uA',
		'privateKey' => 'r0oleUNyBPC5SnunmgAvUMgXW0hzmP4_778bvbsSATE',
	],
];

// Web-Push-Objekt initialisieren
$webPush = new \Minishlink\WebPush\WebPush($auth);



// Payload vorbereiten
$payload = [
	"title"	=> "Fehlende Rückmeldung!",
	"body"	=> $argv[2] . " " . $argv[3],
	"badge"	=> "https://spzroenkhausen.bplaced.net/static/media/4.95cce34e11d6b0d3b99c.png",
	"icon"	=> "https://spzroenkhausen.bplaced.net/static/media/4.95cce34e11d6b0d3b99c.png",
	"image"	=> "https://spzroenkhausen.bplaced.net/static/media/4.95cce34e11d6b0d3b99c.png",
	"vibrate"	=> [300, 100, 400]
];

foreach($subscriptions as $sub){
	// Subscription des Users
	$subscription = \Minishlink\WebPush\Subscription::create([
		"endpoint" => $sub->endpoint,
		"publicKey" => $sub->publicKey,
		"authToken" => $sub->authToken,
	]);

	// Notification vorbereiten
	$result = $webPush->queueNotification(
	$subscription,
	json_encode($payload)
);
}

$error = 0;

// delete-options
$options = [
	'http' => [
		'method' => 'DELETE',
		'header' => 'Content-type: application/x-www-form-urlencoded'
	]
];

// Notification senden
echo "---" . count($subscriptions) . "---\n";
foreach ($webPush->flush() as $report) {
    $endpoint = $report->getRequest()->getUri()->__toString();
    if ($report->isSuccess()) {
        echo "[y] OK for subscription {$endpoint}\n";
    } else {
		$error = $error + 1;
        echo "[x] Message failed to sent for subscription {$endpoint}: {$report->getReason()}\n";
		echo "    Deleting subscription\n";
		foreach($subscriptions as $sub){
			if ($sub->endpoint == $endpoint) {
				$context = stream_context_create($options);
				$result = file_get_contents($url . '/api/v0/pushsubscription/' . $sub->subscription_id . '?api_token=0eef5dacbf418992610dbf2bf593f57c', false, $context);
				var_dump($result);
			}
		}
    }
}
echo "-------\n";

send_single_push(count($subscriptions), $error);

?>
