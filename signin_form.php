<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Registrazione</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {
            background: linear-gradient(135deg, #6a11cb 0%, #2575fc 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .card {
            border-radius: 1rem;
            box-shadow: 0 4px 24px rgba(0,0,0,0.15);
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="row justify-content-center">
            <div class="col-md-5">
                <div class="card p-4 mt-5">
                    <h2 class="text-center mb-4">Registrazione</h2>
                    <?php if (isset($_GET['errore'])): ?>
                        <div class="alert alert-danger text-center" role="alert">
                            <?php echo htmlspecialchars($_GET['errore']); ?>
                        </div>
                    <?php endif; ?>
                    <?php if (isset($_GET['successo'])): ?>
                        <div class="alert alert-success text-center" role="alert">
                            <?php echo htmlspecialchars($_GET['successo']); ?>
                        </div>
                    <?php endif; ?>
                    <form action="singin.php" method="POST">
                        <div class="mb-3">
                            <label for="username" class="form-label">Username</label>
                            <input type="text" class="form-control" id="username" name="username" required>
                        </div>
                        <div class="mb-3">
                            <label for="password" class="form-label">Password</label>
                            <input type="password" class="form-control" id="password" name="password" required>
                        </div>
                        <div class="mb-3">
                            <label for="ruolo" class="form-label">Ruolo</label>
                            <select class="form-select" id="ruolo" name="ruolo" required>
                                <option value="">Seleziona ruolo</option>
                                <option value="Insegnante">Insegnante</option>
                                <option value="Studente">Studente</option>
                                <option value="Segreteria">Segreteria</option>
                            </select>
                        </div>
                        <button type="submit" class="btn btn-success w-100">Registrati</button>
                    </form>
                    <div class="text-center mt-3">
                        <span>Hai già un account? <a href="login_form.php">Accedi qui</a></span>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>