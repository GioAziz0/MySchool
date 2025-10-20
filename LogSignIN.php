<?php
// File JSON dove sono salvati gli utenti
$usersPassFile = __DIR__ . '/users.json';
// "Pepper" segreto per aumentare la sicurezza delle password
$pepper = 'inserisciQuiUnPepperSicuro';

// Carica utenti dal file JSON
function get_users($usersPassFile) {
    if (!file_exists($usersPassFile)) return [];
    $json = file_get_contents($usersPassFile);
    $users = json_decode($json);
    return is_array($users) ? $users : [];
}

// Funzione di login
function login($username, $password) {
    global $usersPassFile, $pepper;
    $users = get_users($usersPassFile);
    $password_hash = hash('sha256', $password);
    $pp = hash('sha256', $pepper);
    foreach($users as $user) {
        if (!isset($user->username) || !isset($user->password)) continue;
        $salt = substr($user->password, 0, 32);
        $expected = $salt . $password_hash . $pp;
        if($user->username === $username && $user->password === $expected) {
            return true;
        }
    }
    return false;
}

// Funzione di registrazione
function signin($username, $password) {
    global $usersPassFile, $pepper;
    $users = get_users($usersPassFile);
    // Controlla se l'utente esiste già
    foreach($users as $user) {
        if(isset($user->username) && $user->username === $username) {
            return false; // Username già esistente
        }
    }
    $salt = bin2hex(random_bytes(16));
    $password_hash = hash('sha256', $password);
    $pp = hash('sha256', $pepper);
    $newUser = new stdClass();
    $newUser->username = $username;
    $newUser->password = $salt . $password_hash . $pp;
    $users[] = $newUser;
    file_put_contents($usersPassFile, json_encode($users, JSON_PRETTY_PRINT));
    return true;
}

?>