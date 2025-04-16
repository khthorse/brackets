
# Beerpong Turnering

Et grafisk Python-program for å administrere et beerpong-turneringsoppsett, inkludert gruppespill, sluttspill og visuell visning av kampoppsett og lagresultater. Programmet inkluderer også nedtellingstimere for bordene.

## 📸 Funksjoner

- Gruppespill og sluttspill med automatisk kampgenerering
- Visualisering av turneringsbraketter og tabeller
- Kontrollpanel for å sette inn lag, endre kamptid, velge vinnere, og redigere kampoppsett
- To nedtellingstimere med sirkulær visning
- Mulighet for å legge til laglogoer

## 🛠️ Krav

- Python 3.12 eller nyere

### Avhengigheter

Installér nødvendige pakker med pip:

```bash
pip install customtkinter pillow
```

> `customtkinter` brukes for moderne GUI-elementer  
> `pillow` brukes for håndtering og visning av bildefiler

## 🚀 Hvordan kjøre programmet

Kjør `main.py`:

```bash
python main.py
```

Dette åpner hovedvinduet med timerne og turneringsbraketten.

### Alternativt: Kun timer

Du kan også kjøre `timer.py` alene for å kun bruke timer-funksjonaliteten:

```bash
python timer.py
```

## 📁 Filstruktur

```text
.
├── main.py           # Hovedfilen for hele beerpong-turneringen
├── brackets.py       # All logikk for turneringsmodell og GUI
├── timer.py          # Timer-modul med visuell nedtelling
├── menageriet_logo.png   # (valgfritt) Logo for turneringen
```

## 💡 Tips

- Du kan legge til laglogoer ved å krysse av i kontrollvinduet.
- Lagene som legges inn i tekstboksen i kontrollvinduet brukes både til gruppespill og sluttspill.
- Programmet beregner automatisk vinnere, statistikk og rangerer lagene etter poeng og differanse.

