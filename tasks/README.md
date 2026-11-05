# RideMore Adventure Engine – dokumentacja zadań

Ten katalog zawiera instrukcje wykonawcze dla programisty. Każdy plik TASK-XX opisuje zakres, istniejące rozwiązania do ponownego wykorzystania, kontrakty, zależności, sposób realizacji, obsługę braków danych i błędów oraz kryteria odbioru.

## Kolejność i bramki

| Plik | Zadanie | Warunek rozpoczęcia |
|---|---|---|
| [TASK-00](TASK-00-UX-MOCKUPS.md) | Audyt istniejącego UI, mockupy i akceptacja | Bezwarunkowo pierwsze |
| [TASK-01](TASK-01-DATA-CONTRACTS.md) | Kontrakty danych i DTO | Wyraźna akceptacja Task 0 |
| [TASK-02](TASK-02-GPX-ANALYZER.md) | Analiza GPX i profilu trasy | Task 1 |
| [TASK-03](TASK-03-STAGE-PLANNER.md) | Podział trasy na etapy | Task 1 i 2 |
| [TASK-04](TASK-04-STAGE-DEMAND-MODEL.md) | Czas, fizyka jazdy i zapotrzebowanie etapu | Task 1–3 |
| [TASK-05](TASK-05-ADVENTURE-ENGINE-INTEGRATION.md) | Eksperci, obciążenie i rekomendacje | Task 1–4 |
| [TASK-06](TASK-06-PHP-SERVICE-API.md) | Serwis orkiestrujący i API | Task 1–5 |
| [TASK-07](TASK-07-PLANNER-UI-INTEGRATION.md) | Integracja z istniejącym planerem | Task 0 zaakceptowany, API gotowe |
| [TASK-08](TASK-08-VALIDATION-AND-RELEASE.md) | Testy end-to-end i walidacja | Task 1–7 |

## Wspólne reguły obowiązujące we wszystkich zadaniach

1. Rozwijamy istniejący Ridemore. Najpierw sprawdzamy i wykorzystujemy istniejące widoki, komponenty, mapę, planer, modele i biblioteki.
2. Nie tworzymy równoległego planera ani nie przeprowadzamy dużej przebudowy bez wcześniejszego uzasadnienia i zgody właściciela produktu.
3. Python w `tests/` jest implementacją referencyjną/testową. Produkcyjny runtime ma działać w PHP; nie dodajemy zależności od uruchamiania Pythona na serwerze.
4. Liczba dni zadana przez użytkownika jest wiążąca. System nie zmienia jej automatycznie i nie blokuje planu z powodu trudności. Pokazuje konsekwencje, obciążenie i ostrzeżenia.
5. Nieznane dane nie są zerem. Nie wolno tworzyć fikcyjnych wartości, POI, dostępności noclegów, sklepów ani punktów wody.
6. Wyniki liczbowe muszą mieć jednostkę, pochodzenie i status: `measured`, `declared`, `calculated`, `estimated` albo `unknown`. W miarę możliwości należy podać również niepewność i wersję modelu.
7. Parametrów, których typowy użytkownik nie umie podać, nie przerzucamy na niego w formularzu. Stosujemy jawne założenia/estymacje z niepewnością albo pozostawiamy wartość nieznaną.
8. Każdy task musi przejść własne testy i kryteria akceptacji. Nie uznajemy samego faktu, że kod się uruchamia, za dowód poprawności.
9. Zmiana zakresu, architektury lub istniejącego zachowania wymaga opisania wpływu i uzgodnienia z właścicielem produktu.

## Aktualny stan repozytorium

- `adventure_knowledge.json` zawiera bazę wiedzy, reguły i kontrakty eksperckie.
- `wizard_questions.json` zawiera kontrakt pytań wizarda i źródeł prefill.
- `tests/adventure_engine_runner.py` jest referencyjnym interpreterem reguł.
- `tests/route_stage_planner.py` jest prototypem analizy GPX i podziału etapów w Pythonie.
- `tests/kotlina400-bikepacking-route.gpx` jest głównym rzeczywistym fixture do testów.
- Repozytorium nie zawiera jeszcze produkcyjnego silnika PHP ani potwierdzonej integracji z runtime Ridemore. Zadania PHP są specyfikacją przyszłej implementacji, a nie opisem już istniejącego kodu.

Przed implementacją każdego taska wykonawca ma sprawdzić aktualny stan branchu i rzeczywiste pliki. Nazwy klas i ścieżki PHP podane w specyfikacjach są proponowanym kontraktem, który należy dopasować do istniejącej struktury Ridemore, zamiast tworzyć drugi system.
