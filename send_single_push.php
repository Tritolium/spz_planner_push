<?php

require __DIR__ . '/vendor/autoload.php';

// use Minishlink\Webpush\Webpush;

function send_single_push($devices, $error = 0)
{
	$url = 'https://spzroenkhausen.bplaced.net';

	$auth = [
		'VAPID' => [
			'subject' => 'https://tritolium.github.io',
			'publicKey' => 'BD0AbKmeW7bACNzC9m0XSUddJNx--VoOvU2X0qBF8dODOBhHvFPjrKJEBcL7Yk07l8VpePC1HBT7h2FRK3bS5uA',
			'privateKey' => 'r0oleUNyBPC5SnunmgAvUMgXW0hzmP4_778bvbsSATE',
		],
	];

	// Web-Push-Objekt initialisieren
	$webPush = new \Minishlink\WebPush\WebPush($auth);

	$body = ($devices == 0) ? "Kein Push verschickt" : 
		(($devices == 1) ? "Push an 1 Gerät verschickt" : 
		"Push an " . $devices . " Geräte verschickt");
	
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

	// Subscription des Users, member_id 3
	$admin_subscriptions = json_decode(file_get_contents($url . '/api/v0/pushsubscription?member_id=3&api_token=0eef5dacbf418992610dbf2bf593f57c'));

	foreach($admin_subscriptions as $sub){
		// Subscription des Users
		$subscription = \Minishlink\WebPush\Subscription::create([
			"endpoint" => $sub->endpoint,
			"publicKey" => $sub->publicKey,
			"authToken" => $sub->authToken,
		]);

		// Notification vorbereiten
		$webPush->queueNotification(
			$subscription,
			json_encode($payload)
		);
	}

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
			foreach($admin_subscriptions as $sub){
				if ($sub->endpoint == $report->getRequest()->getUri()->__toString()) {
					echo "Fehler bei {$sub->endpoint}, lösche Subscription\n";
					// Subscription löschen
					$options = [
						'http' => [
							'method' => 'DELETE',
							'header' => 'Content-Type: application/x-www-form-urlencoded',
						],
					];

					$context = stream_context_create($options);
					$result = file_get_contents($url . '/api/v0/pushsubscription/' . $sub->subscription_id . '?api_token=0eef5dacbf418992610dbf2bf593f57c', false, $context);
					var_dump($result);
				}
			}
			echo "Fehler: {$report->getReason()}\n";
		}
	}
}

?>
