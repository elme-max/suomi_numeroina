# Suomi numeroina

Itsestään päivittyvä dashboard Suomen talouden tärkeimmistä tunnusluvuista:

| Tunnusluku | Sarja | Tilastokeskuksen taulukko |
|---|---|---|
| Työllisyysaste | 20–64-vuotiaat, trendi, kuukausittain | työvoimatutkimus, `135z` |
| Työttömyysaste | 15–74-vuotiaat, trendi, kuukausittain | työvoimatutkimus, `135z` |
| Nuorisotyöttömyysaste | 15–24-vuotiaat, trendi, kuukausittain | työvoimatutkimus, `135z` |
| Bruttokansantuote | volyymi, neljännesvuosittain | neljännesvuositilinpito, `132h` |
| Työn tuottavuus | BKT:n volyymi / tehdyt työtunnit, kausitasoitettu | neljännesvuositilinpito, `132h` ja `11tj` |
| Teollisuuden uudet tilaukset | arvoindeksi 2021 = 100, kuukausittain | teollisuuden uudet tilaukset, `14mi` |

Kaikki luvut tulevat Tilastokeskuksen maksuttomasta ja avoimesta
[StatFin-rajapinnasta](https://pxdata.stat.fi/PxWeb/pxweb/fi/StatFin/) (CC BY 4.0). API-avainta ei tarvita.

## Yksityinen käyttö omalta koneelta

Sivu toimii suoraan tiedostona, palvelinta tai julkaisua ei tarvita. Tarvitset vain Pythonin (3.8+).

Hae tuoreet luvut suoraan Tilastokeskuksesta ja avaa dashboard selaimeen:

```bash
python3 scripts/fetch_data.py --avaa
```

Windowsissa komento on `py scripts\fetch_data.py --avaa`. Komennosta voi tehdä työpöydälle
pikakuvakkeen, jolloin dashboard päivittyy ja aukeaa kaksoisnapsautuksella.

Vaihtoehtoisesti voit avata `index.html`-tiedoston sellaisenaan ja päivittää luvut komennolla
`git pull`: GitHub Actions tallentaa tuoreen datan repoon päivittäin.

## Miten automaattipäivitys toimii

1. GitHub Actions -työnkulku (`.github/workflows/update.yml`) ajetaan joka päivä.
2. `scripts/fetch_data.py` hakee tuoreet sarjat ja kirjoittaa ne tiedostoihin `data/data.json`
   ja `data/data.js`. Tiedostot commitoidaan vain, jos Tilastokeskuksen luvut ovat muuttuneet.

## Julkinen julkaisu (valinnainen)

Sivua ei julkaista minnekään oletuksena. Jos haluat sen GitHub Pagesiin (osoite on julkinen):

1. **Settings → Pages → Build and deployment → Source: GitHub Actions**
2. **Settings → Secrets and variables → Actions → Variables**: lisää muuttuja `PUBLISH_PAGES` arvolla `true`

Riippuvuuksia ei ole: skripti käyttää vain Pythonin standardikirjastoa ja sivu on yksi HTML-tiedosto.
