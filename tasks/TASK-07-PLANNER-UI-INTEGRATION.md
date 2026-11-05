# TASK 07 – Integracja z istniejącym planerem Ridemore

**Cel:** podłączyć Adventure Engine do istniejącego planera i wyświetlić wyniki zgodnie z mockupami zaakceptowanymi w Task 0.

## Warunki rozpoczęcia

- Task 0 zaakceptowany;
- Task 1–6 odebrane;
- API działa i ma stabilny kontrakt;
- wykonawca ponownie sprawdzi aktualny kod planera i dopasuje integrację do jego rzeczywistej architektury.

## Zasada nadrzędna

Nie tworzyć nowego planera ani równoległego interfejsu. Rozszerzyć obecne ekrany i komponenty w najmniejszym koniecznym zakresie. Każde odstępstwo od zaakceptowanych mockupów lub duża zmiana istniejącego UI wymaga zgody właściciela produktu.

## Zakres

1. Dodać uruchomienie Adventure Engine z istniejącego planera.
2. Przekazać wybrany GPX/trasę, liczbę dni, profil rowerzysty, dane sprzętu i założenia zgodnie z kontraktem.
3. Automatycznie uzupełnić dane z istniejącego profilu, historii jazd i źródeł Ridemore tylko tam, gdzie adapter rzeczywiście udostępnia dane.
4. Pokazać stan analizy: oczekiwanie, sukces, sukces z estymacjami, brak danych, błąd i możliwość ponowienia.
5. Wyświetlić mapę, profil wysokości, granice etapów, karty dzienne i rekomendacje przy użyciu istniejących komponentów.
6. Oznaczać measured/declared/calculated/estimated/unknown w sposób zrozumiały dla użytkownika; szczegóły techniczne mogą być rozwijane.
7. Umożliwić zmianę liczby dni i parametrów, ponowne wysłanie żądania i odświeżenie wyników.
8. Zachować dane formularza przy błędzie sieci i umożliwić ponowienie bez utraty pracy.
9. Nie pokazywać fikcyjnej dostępności POI. Oznaczać punkty wymagające potwierdzenia.
10. Zapewnić responsywność desktop/mobile zgodną z zaakceptowanymi mockupami.

## Zachowanie krytyczne

- UI nigdy samodzielnie nie zmienia liczby dni.
- Po zmianie parametrów stary wynik musi być oznaczony jako nieaktualny do czasu otrzymania nowego.
- W czasie oczekiwania nie wolno prezentować poprzedniego wyniku tak, jakby dotyczył nowych parametrów.
- Błędy walidacji wskazują pole; awaria API daje możliwość ponowienia.
- Brak danych pokazujemy jako brak/nieznane, nie jako 0.

## Testy i kryteria odbioru

- testy przepływu od istniejącego planera do wyniku;
- testy desktop i mobile;
- test zmiany liczby dni i ponownego przeliczenia;
- test stanu loading, empty, partial/estimated, error i success;
- test zachowania formularza po błędzie sieci;
- test zgodności ekranów z zaakceptowanymi mockupami;
- test, że UI nie wykonuje samodzielnie obliczeń fizycznych i nie zmienia liczby dni;
- test, że niezweryfikowane POI nie są prezentowane jako potwierdzone zaopatrzenie.

**Odbiór:** funkcjonalność jest częścią istniejącego planera, a nie osobną aplikacją; zachowanie odpowiada zaakceptowanemu projektowi.
