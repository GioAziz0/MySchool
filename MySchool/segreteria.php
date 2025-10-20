<?php
session_start();
if (!isset($_SESSION["username"]) || $_SESSION["role"] !== "Segreteria") {
    header("Location: login_form.php");
    exit();
}
?>
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no" />
    <title>Area Segreteria</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {
            background: linear-gradient(135deg, #f7971e 0%, #ffd200 100%);
            min-height: 100vh;
        }
        .main-card {
            border-radius: 1.5rem;
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
            background: rgba(255,255,255,0.95);
            margin-top: 60px;
        }
        .logout-btn {
            position: absolute;
            top: 20px;
            right: 30px;
        }
        .role-title {
            font-weight: 700;
            font-size: 2.2rem;
            letter-spacing: 1px;
            color: #f7971e;
        }
        .custom-list {
            font-size: 1.1rem;
        }
    </style>
</head>
<body>
    <a href="index.php?logout=1" class="btn btn-outline-danger logout-btn">Logout</a>
    <div class="container d-flex justify-content-center align-items-center min-vh-100">
        <div class="main-card p-5 w-100" style="max-width: 600px;">
            <div class="text-center mb-4">
                <span class="role-title">Area Segreteria</span>
            </div>
            <ul class="custom-list">
                <li>Gestione iscrizioni e anagrafiche studenti</li>
                <li>Visualizzazione e modifica orari delle lezioni</li>
                <li>Gestione comunicazioni scuola-famiglia</li>
            </ul>
        </div>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
 
