<?php
session_start();
if (!isset($_SESSION["username"])) {
	header("Location: login_form.php");
	exit();
}

if (isset($_GET['logout'])) {
	session_destroy();
	header("Location: login_form.php");
	exit();
}

// Se la sessione è attiva, controlla e imposta il ruolo se non presente
if (!isset($_SESSION["role"])) {
	$usersdata = json_decode(file_get_contents(__DIR__ . "/usersdata.json"));
	$ruolo = "";
	foreach ($usersdata as $utente) {
		if (isset($utente->username) && $utente->username === $_SESSION["username"]) {
			$ruolo = isset($utente->ruolo) ? $utente->ruolo : "";
			break;
		}
	}
	$_SESSION["role"] = $ruolo;
}

// Redirect in base al ruolo
switch ($_SESSION["role"]) {
	case "Insegnante":
		header("Location: insegnante.php");
		exit();
	case "Studente":
		header("Location: studente.php");
		exit();
	case "Segreteria":
		header("Location: segreteria.php");
		exit();
	default:
		echo "<h2>Benvenuto, " . htmlspecialchars($_SESSION["username"]) . "!</h2>";
		break;
}

