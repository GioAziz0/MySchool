<?php


$usersfile = "usersdata.json";
if (file_exists($usersfile)) {
    $usersdata = json_decode(file_get_contents($usersfile));
    if (!is_array($usersdata)) $usersdata = [];
} else {
    $usersdata = [];
}

require "LogSignIN.php";

// -- Raccolta variabili


$username = $_POST["username"];
$password = $_POST["password"];
$ruolo = isset($_POST["ruolo"]) ? $_POST["ruolo"] : "";



// -- Controllo parametri per la registrazione


// Controllo se username già esistente in usersdata.json
foreach ($usersdata as $utente) {
    if (isset($utente->username) && $utente->username === $username) {
        error_log("Username già esistente");
        header("Location: signin_form.php?errore=Username gia esistente");
        die();
    }
}



if (empty($username) || empty($password) || empty($ruolo)) {
    header("Location: signin_form.php?errore=Compila%20tutti%20i%20campi");
    exit();
}

// -- Salvataggio informazioni di login (solo username e password nel file gestito da LogSingIN.php)
signin($username, $password);




// -- Salvataggio altre informazioni (username e ruolo in usersdata.json)
$newUser = new stdClass();
$newUser->username = $username;
$newUser->ruolo = $ruolo;
$usersdata[] = $newUser;
file_put_contents($usersfile, json_encode($usersdata, JSON_PRETTY_PRINT));

// Redirect dopo registrazione (ad esempio al login)
header("Location: signin_form.php?successo=Registrazione%20avvenuta%20con%20successo");
exit();

?>
