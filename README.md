# Suomi numeroina

Itsestään päivittyvä dashboard Suomen talouden tärkeimmistä tunnusluvuista:

| Tunnusluku | Sarja | Tilastokeskuksen taulukko |
|---|---|---|
| Työllisyysaste | 20–64-vuotiaat, trendi, kuukausittain | työvoimatutkimus, `135z` |
| Työttömyysaste | 15–74-vuotiaat, trendi, kuukausittain | työvoimatutkimus, `135z` |
| Bruttokansantuote | volyymi, neljännesvuosittain | neljännesvuositilinpito, `132h` |
| Työn tuottavuus | BKT:n volyymi / tehdyt työtunnit, kausitasoitettu | neljännesvuositilinpito, `132h` ja `11tj` |
| Teollisuuden uudet tilaukset | arvoindeksi 2021 = 100, kuukausittain | teollisuuden uudet tilaukset, `14mi` |

Kaikki luvut tulevat Tilastokeskuksen maksuttomasta ja avoimesta
[StatFin-rajapinnasta](https://pxdata.stat.fi/PxWeb/pxweb/fi/StatFin/) (CC BY 4.0). API-avainta ei tarvita.

## Miten päivitys toimii

1. GitHub Actions -työnkulku (`.github/workflows/update.yml`) ajetaan joka päivä.
2. `scripts/fetch_data.py` hakee tuoreet sarjat ja kirjoittaa ne tiedostoon `data/data.json`.
   Tiedosto commitoidaan vain, jos Tilastokeskuksen luvut ovat muuttuneet.
3. Sivu (`index.html` + `data/`) julkaistaan GitHub Pagesiin.

## Käyttöönotto

Valitse repossa **Settings → Pages → Build and deployment → Source: GitHub Actions**.
Sen jälkeen työnkulku julkaisee sivun osoitteeseen `https://<käyttäjä>.github.io/suomi_numeroina/`.
Työnkulun voi käynnistää myös käsin Actions-välilehdeltä (*Run workflow*).

## Paikallinen käyttö

```bash
python3 scripts/fetch_data.py
```

```bash
python3 -m http.server 8000
```

Avaa sitten `http://localhost:8000`. Riippuvuuksia ei ole: skripti käyttää vain Pythonin
standardikirjastoa ja sivu on yksi HTML-tiedosto.
