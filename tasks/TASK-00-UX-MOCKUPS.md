# TASK 00 – Audyt istniejącego UI, mockupy i akceptacja

**Typ:** UX/UI i produkt  
**Status:** obowiązkowy, blokujący  
**Cel:** zaprojektować Adventure Engine jako rozszerzenie istniejącego planera Ridemore, bez nieuzasadnionej przebudowy produktu.

## Punkt wyjścia

Przed projektowaniem należy obejrzeć i zinwentaryzować istniejący planer, mapę, profile tras, formularze, komponenty, nawigację, style oraz widoki desktop/mobile. Trzeba sprawdzić istniejące rozwiązania w działającej aplikacji i kodzie, a nie opierać się wyłącznie na opisach repozytorium.

## Zakres prac

1. Sporządzić tabelę: istniejący ekran/komponent → możliwość ponownego użycia → minimalna wymagana zmiana.
2. Narysować przepływ użytkownika od uruchomienia doradcy do zapisanego planu.
3. Przygotować obowiązkowe mockupy M0.1–M0.8:
   - M0.1 wejście do doradcy i rozpoczęcie/ponowienie planowania;
   - M0.2 analiza GPX: mapa, dystans, przewyższenie, profil, jakość danych;
   - M0.3 założenia wyprawy: liczba dni, preferencje, rower, bagaż i doświadczenie;
   - M0.4 profil rowerzysty i podsumowanie danych zadeklarowanych oraz automatycznie uzupełnionych;
   - M0.5 podział trasy na etapy, mapa granic, dystans, przewyższenie, czas i obciążenie;
   - M0.6 szczegóły jednego dnia: profil, czas, energia, CHO, płyny, bezpieczeństwo i regeneracja;
   - M0.7 centrum rekomendacji: priorytety, uzasadnienie, status danych i niepewność;
   - M0.8 końcowe podsumowanie całej wyprawy, lista przygotowań i powrót do edycji.
4. Każdy mockup pokazać w układzie desktop i mobile. Wykorzystać istniejące komponenty i styl Ridemore, o ile to możliwe.
5. Pokazać stany: dane kompletne; dane szacunkowe; dane nieznane; brak danych wymagających decyzji; bardzo wymagający plan; POI bez potwierdzonej dostępności; edycja i ponowne przeliczenie.
6. Użyć Kotlina400 jako scenariusza demonstracyjnego. Dane, których repozytorium nie potwierdza, oznaczyć jako przykładowe.
7. Przygotować listę proponowanych zmian większych niż kosmetyczne, z uzasadnieniem, wpływem na obecny planer i wariantem minimalnym.

## Zasady UX

- Nie projektować nowego, niezależnego planera.
- Nie zmieniać bez zgody głównej nawigacji, istniejących bibliotek ani architektury.
- Liczba dni podana przez użytkownika pozostaje niezmienna, nawet gdy plan jest trudny. UI pokazuje konsekwencje, a nie blokadę.
- Nie pytać użytkownika o parametry eksperckie, których przeciętnie nie zna. Pokazać przyjęte założenie i niepewność.
- Nie przedstawiać znalezionego POI jako potwierdzonego punktu zaopatrzenia bez danych o dostępności/ilości/godzinach.

## Rezultaty

- osiem kompletnych mockupów;
- desktop i mobile;
- mapa przepływu użytkownika;
- opis interakcji i stanów;
- tabela ponownego wykorzystania istniejących rozwiązań;
- lista zmian wymagających decyzji właściciela.

## Kryteria odbioru

Każdy M0.1–M0.8 musi zostać przedstawiony właścicielowi produktu. Task jest zakończony dopiero po wyraźnej akceptacji wszystkich mockupów i przepływu. Uwagi należy nanieść i ponownie przedstawić zmienione ekrany.

**TWARDY STOP:** bez jednoznacznej akceptacji właściciela produktu nie wolno rozpocząć Task 1, projektowania DTO ani implementacji PHP. Milczenie nie oznacza akceptacji. Akceptacja mockupów nie jest zgodą na nieuzgodnione zmiany architektury.
