from django.shortcuts import render
from django.http import HttpRequest, HttpResponse
from models import *
from datetime import datetime
from typing import Optional, List, Dict, Any

# Create your views here.

# =====================================================================
# SEZIONE DOCENTI: Gestione classi e didattica
# =====================================================================

def studenti_classe(classe: Classe):
    """
    Restituisce la lista di studenti in una classe
    """
    ...

def consiglio_di_classe(classe: Classe):
    """
    Restituisce la lista di insegnanti che insegnano in una classe
    """
    ...

def appello(classe: Classe, data: datetime = datetime.today()):
    """
    Restituisce l'appello di una determinata classe in un determinato giorno
    """ 
    ...

def salva_appello(request: HttpRequest, classe: Classe, presenze: Dict[Studente, str], data: datetime = datetime.today()):
    """
    Salva o aggiorna l'appello di una classe assegnando presenze, assenze e ritardi.
    Permessi: Solo il docente responsabile della classe in quell'ora, Dirigente o Ufficio Tecnico.
    """
    ...

def aggiungi_modifica_voto(request: HttpRequest, studente: Studente, materia: Materia, voto: float, data: datetime, commento: Optional[str] = None):
    """
    Aggiunge o modifica la valutazione di uno studente per una specifica materia.
    Affinché la webapp sia scalabile, il dato deve essere tracciato tramite identificativo della valutazione.
    Permessi: Solo il docente della materia specifica o il Dirigente/Ufficio Tecnico.
    """
    ...

def rimuovi_voto(request: HttpRequest, id_voto: int):
    """
    Rimuove un voto precedentemente assegnato.
    Permessi: Solo l'autore del voto o Ufficio Tecnico/Dirigente.
    """
    ...

def aggiungi_nota(request: HttpRequest, studente: Studente, testo: str, disciplinare: bool = False):
    """
    Aggiunge una nota comportamentale o didattica a uno studente.
    Permessi: Docenti della classe, Dirigente o Ufficio Tecnico.
    """
    ...

def assegna_compito(request: HttpRequest, classe: Classe, materia: Materia, descrizione: str, data_consegna: datetime, allegati: Optional[List[Any]] = None):
    """
    Assegna un compito alla classe, integrando anche caricamento e gestione materiale didattico (simile a Classroom).
    Permessi: Docente della materia o Dirigente.
    """
    ...

def aggiorna_calendario_classe(request: HttpRequest, classe: Classe, evento: Any, azione: str = 'aggiungi'):
    """
    Aggiunge, modifica o rimuove eventi nel calendario specifico della classe.
    Permessi: Docenti della classe, Dirigente, Ufficio Tecnico.
    """
    ...


# =====================================================================
# SEZIONE STUDENTI / GENITORI: Visualizzazione e interazione
# =====================================================================

def voti_studente(Studente: Studente, Periodo: periodoScolasticoStudente = None, Materia: Materia = None):
    """
    Restituisce i voti di uno studente.
    Il parametro periodo permette di scegliere per quale periodo filtrare i risultati (di base mostra i voti dell'anno scolastico corrente)
    Il parametro materia permette di filtrare per una materia specifica
    Attenzione: La funzione restituisce solo i voti per i quali si dispone i permessi di visualizzazione
    """
    ...

def note_studente(Studente: Studente, Periodo: periodoScolasticoStudente = None, Disciplinare: bool = None):
    """
    Restituisce i voti di uno studente.
    Il parametro periodo permette di scegliere per quale periodo filtrare i risultati (di base mostra le note dell'anno scolastico corrente)
    Attenzione: La funzione restituisce solo le note per le quali si dispone i permessi di visualizzazione
    """
    ...

def assenze_ritardi_studente(request: HttpRequest, studente: Studente, periodo: Optional[periodoScolasticoStudente] = None):
    """
    Restituisce la lista di assenze, ritardi e uscite anticipate di uno studente.
    Permessi: Studente stesso (sola visualizzazione), Genitore, Docenti, Segreteria, Ufficio Tecnico.
    """
    ...

def giustifica_assenza_ritardo(request: HttpRequest, id_assenza_ritardo: int, motivazione: str):
    """
    Permette a un genitore (o studente maggiorenne) di giustificare un'assenza o un ritardo.
    Permessi: Genitore associato o studente maggiorenne.
    """
    ...

def compiti_studente(request: HttpRequest, studente: Studente, stato: Optional[str] = None):
    """
    Restituisce i compiti assegnati allo studente. Filtrabili per stato (da fare, completati, in ritardo).
    Permessi: Studente, Genitore, Docenti.
    """
    ...

def consegna_compito(request: HttpRequest, id_compito: int, allegati: List[Any]):
    """
    Permette allo studente di consegnare un compito caricando file e documentazione.
    Permessi: Solo lo studente a cui è assegnato il compito.
    """
    ...

def firma_digitale_documento(request: HttpRequest, id_documento: int, dati_firma: Any):
    """
    Permette la compilazione, firma digitale o presa visione di circolari e documenti.
    Permessi: Genitore o studente maggiorenne (se il documento li riguarda), oppure Docente/Segreteria.
    """
    ...

def visualizza_circolari(request: HttpRequest):
    """
    Visualizza la documentazione/circolari indirizzate all'utente richiedente.
    Permessi: Qualsiasi utente autenticato (studente, genitore, docente).
    """
    ...

# =====================================================================
# SEZIONE AMMINISTRAZIONE: Segreteria, Ufficio Tecnico, Dirigente
# =====================================================================

def gestione_anagrafica_utenti(request: HttpRequest, id_utente: Optional[int] = None, dati: Optional[Dict[str, Any]] = None, azione: str = 'visualizza'):
    """
    Creazione, lettura, aggiornamento e cancellazione (CRUD) dati anagrafici e account.
    Permessi: 
    - Segreteria: Visualizzazione globale dati anagrafici e modifica limitata.
    - Ufficio Tecnico: Amministrazione e gestione completa account.
    """
    ...

def gestione_classi(request: HttpRequest, id_classe: Optional[int] = None, dati: Optional[Dict[str, Any]] = None, azione: str = 'crea'):
    """
    Crea o modifica i dati di una classe (assegnazione studenti e docenti).
    Permessi: Ufficio Tecnico o Dirigente.
    """
    ...

def gestione_circolari_documenti(request: HttpRequest, titolo: str, contenuto: str, destinatari: List[Any], allegati: Optional[List[Any]] = None):
    """
    Pubblica o aggiorna comunicazioni, documenti e circolari rivolte a specifiche classi, utenti o all'intero istituto.
    Permessi: Dirigente, Ufficio Tecnico, Segreteria.
    """
    ...

def pagamenti_pagopa(request: HttpRequest, id_utente: Optional[int] = None, id_pagamento: Optional[int] = None):
    """
    Interfaccia per visualizzazione e integrazione servizi di pagamento (PagoPa).
    Permessi: 
    - Studente Maggiorenne/Genitore: solo i propri pagamenti.
    - Segreteria: visualizzazione stato e gestione incassi per tutti gli alunni.
    """
    ...

def avvia_anno_scolastico(request: HttpRequest, impostazioni: Dict[str, Any]):
    """
    Avvio di un nuovo anno accademico (gestione passaggi di classe, reset registri e assenze).
    Permessi: ESCLUSIVAMENTE Dirigente scolastico.
    """
    ...