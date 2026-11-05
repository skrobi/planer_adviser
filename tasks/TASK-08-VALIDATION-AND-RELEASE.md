# TASK 08 – Walidacja, testy end-to-end i przygotowanie wydania

**Cel:** wykazać, że cały przepływ od GPX do planu wyprawy działa poprawnie, zachowuje założenia użytkownika i nie prezentuje nieuzasadnionej precyzji.

## Warunki rozpoczęcia

Task 1–7 zakończone. Środowisko testowe ma wersję PHP, konfigurację i dane zbliżone do docelowego Ridemore. Nie testować wyłącznie Pythona – wymagane są testy produkcyjnej ścieżki PHP i UI.

## Zakres walidacji

1. Uruchomić pełny przepływ: request → walidacja → GPX → etapy → model czasu/energii → eksperci → wynik API → UI.
2. Wykorzystać Kotlina400 jako główny fixture oraz syntetyczne GPX o znanych parametrach.
3. Wykonać testy porównawcze Python/PHP dla tych samych wejść. Tolerancje ustalić dla każdej wielkości osobno; nie używać jednej arbitralnej tolerancji dla wszystkiego.
4. Zweryfikować sumy dystansu, przewyższenia, ciągłość geometrii, liczbę etapów, granice i kolejność.
5. Zweryfikować spójność zmian: inna masa, kalibracja, liczba dni, wiatr lub nawierzchnia powinny zmieniać właściwe wyniki w oczekiwanym kierunku.
6. Sprawdzić skrajne przypadki: bardzo krótka/długa trasa, jeden dzień, wiele dni, dni z bardzo dużym przewyższeniem, brak elewacji, błędny GPX, brak profilu i nieznana masa bagażu.
7. Zweryfikować rekomendacje bezpieczeństwa, kumulację obciążenia, żywienie, nawodnienie i regenerację.
8. Sprawdzić, czy brak zapasu jedzenia nie generuje ostrzeżenia o niewystarczającym zapasie.
9. Sprawdzić, czy brak danych o POI nie generuje fikcyjnych punktów, dostępności lub noclegów.
10. Sprawdzić stany UI, responsywność, obsługę błędów API i możliwość ponowienia.
11. Zmierzyć czas i zużycie pamięci dla GPX o różnych rozmiarach oraz sprawdzić limity.
12. Przygotować raport ograniczeń modelu, ryzyk i znanych błędów.

## Wymagane scenariusze akceptacyjne

- **A. Plan zgodny z możliwościami:** system przedstawia etapy i rekomendacje.
- **B. Trudny plan na małą liczbę dni:** liczba dni pozostaje taka, jak podał użytkownik; UI pokazuje bardzo duże obciążenie i konsekwencje.
- **C. Brak danych o bagażu:** nie podstawia arbitralnej masy jako deklaracji użytkownika; niepewność jest widoczna.
- **D. Brak CP/FTP:** system używa tylko zatwierdzonego fallbacku albo raportuje ograniczenie; nie udaje pomiaru.
- **E. Brak danych o POI:** nie wymyśla miejsc uzupełniania wody, jedzenia i noclegu.
- **F. Nieznany zapas jedzenia:** pokazuje orientacyjne zapotrzebowanie, ale nie twierdzi, że zapas jest niewystarczający.
- **G. Zmiana liczby dni:** przelicza podział i zapotrzebowanie, zachowując nową wartość.
- **H. Błędny GPX / błąd API:** użytkownik dostaje czytelny komunikat, a system nie pokazuje starego wyniku jako aktualnego.

## Kryteria odbioru

- wszystkie testy automatyczne PHP, Python (referencyjne) i UI przechodzą;
- raport porównania PHP/Python zawiera wejścia, tolerancje i odchylenia;
- testy sum i ciągłości trasy przechodzą;
- scenariusze A–H przechodzą;
- brak krytycznych błędów bezpieczeństwa i utraty danych;
- wszystkie ograniczenia i znane niedoskonałości są udokumentowane;
- właściciel produktu otrzymuje demonstrację całego przepływu i raport testów.

**Odbiór:** gotowość do decyzji o wdrożeniu. Samo przejście testów nie oznacza automatycznej zgody na wdrożenie produkcyjne.
