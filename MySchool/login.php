<?php
//INSERISCI la pagina di login
$loginpage = "login_form.php";


require "LogSignIN.php";

try {


    $user = $_POST["username"];
    $pass = $_POST["password"];

    $log = login($user, $pass);


    if ($log) {
        session_start();
        $_SESSION["username"] = $user;
        header("Location: index.php");
        die();
    } else {
        header("Location: " . $loginpage . "?errore=Username%20o%20password%20errati");
        die();
    }

} catch (Exception $e) {
    header("Location: " . $loginpage . "?errore=Errore%20durante%20il%20login");
    die();
}

?>