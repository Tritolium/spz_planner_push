<?php

require __DIR__ . '/vendor/autoload.php';

// use Minishlink\Webpush\Webpush;

$subscriptions = json_decode(file_get_contents('https://spzroenkhausen.bplaced.net/api/attendence.php?api_token=0eef5dacbf418992610dbf2bf593f57c&missing&event_id=' . $argv[1]));



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
	"body"	=> "Für einen heutigen Termin fehlt eine Rückmeldung",
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

// Notification senden
foreach ($webPush->flush() as $report) {
    if ($report->isSuccess()) {
        echo "OK\n";
    } else {
        echo "Fehler: {$report->getReason()}\n";
    }
}

?>
