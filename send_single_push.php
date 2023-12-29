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
		"endpoint" => "https://web.push.apple.com/QNZ3Hfb2te30j98M4W6nlu9EkprCkjZ1T3ZlDL1jVfN7rMd03ohB5VyKfbnvJnc6ILXH5Fe0-4mm2Lh_Z9bXmSttZhIKOriA23ePlecqC44AOqTTagRjWoPz3Dzb5SAJSzB8fMXb-0K0vaP9eOrAeEsG_O9ExbIdnMxvKd-Vfa4",
		"publicKey" => "BKj6A2hXq2oyOLt2eueLXUgVdPD6cd7CKbeIXO47R93gFQHbGkIzZWlaRViYQx5M8D_3r56x53w2z3ldVVV9eVI",
		"authToken" => "Dut34WtemunYi1SP-_CTdQ",
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
