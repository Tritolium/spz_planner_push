<?php

require __DIR__ . '/vendor/autoload.php';

// use Minishlink\Webpush\Webpush;

function send_single_push($devices, $error)
{
	$auth = [
		'VAPID' => [
			'subject' => 'https://tritolium.github.io',
			'publicKey' => 'BD0AbKmeW7bACNzC9m0XSUddJNx--VoOvU2X0qBF8dODOBhHvFPjrKJEBcL7Yk07l8VpePC1HBT7h2FRK3bS5uA',
			'privateKey' => 'r0oleUNyBPC5SnunmgAvUMgXW0hzmP4_778bvbsSATE',
		],
	];

	// Web-Push-Objekt initialisieren
	$webPush = new \Minishlink\WebPush\WebPush($auth);

	$body = "Push an " . $devices . " Geräte verschickt";
	
	if($error > 0){
		$body = $body . ", bei " . $error . " fehlgeschlagen";
	}

	// Payload vorbereiten
	$payload = [
		"title"	=> "Push gesendet",
		"body"	=> $body,
		"badge"	=> "https://spzroenkhausen.bplaced.net/static/media/4.95cce34e11d6b0d3b99c.png",
		"icon"	=> "https://spzroenkhausen.bplaced.net/static/media/4.95cce34e11d6b0d3b99c.png",
		"image"	=> "https://spzroenkhausen.bplaced.net/static/media/4.95cce34e11d6b0d3b99c.png",
		"vibrate"	=> [300, 100, 400]
	];

	// Subscription des Users
	$subscription = \Minishlink\WebPush\Subscription::create([
		"endpoint" => "https://web.push.apple.com/QGZ3jvNz9U_yYNjIrZA2RvQI_cav_eX65cQt1o07ooVThttGkMf9DfHXMdTrkTTVhRDlg6syrAIMfMtrRiLcum6OhQ-CUcxfFDsWF3VzMLj7WcracVm2M22MPvwMaL-t_R--CB3TL_jJHX2PPnGowc1_w9alV0mw7eGdOerccec",
		"publicKey" => "BI5fwWK0qFuFXme06s-5Jgobwbjgiysqk4x6ddbfvvdQ_uXjOObFwFmur0YH8NOpbUpFVRQgr8qrtkB75UUIB6I",
		"authToken" => "9gd7bSEebqlCvQnChpIlpg",
	]);

	// Notification vorbereiten
	$result = $webPush->queueNotification(
		$subscription,
		json_encode($payload)
	);

	// Notification senden
	foreach ($webPush->flush() as $report) {
		if ($report->isSuccess()) {
			echo "OK\n";
		} else {
			echo "Fehler: {$report->getReason()}\n";
		}
	}
}

?>
