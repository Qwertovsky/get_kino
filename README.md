Due to redesign of kinoposik.ru it's almost impossible to use it now.
The most important information there is user ratings and I would like to backup mine.

So here you can find a simple script to retrieve movie ratings for specific user.
Ratings with movie name, linke to image and link to kinopoisk page are stored in local sqlite database kinopoisk.db .

#### load.py
Самостоятельно загружает данные со страницы пользователя по его id.
Результат записывает в базу SQLite.

#### parse_ratings.py
Обрабатывает сохранённую страницу оценок пользователя.
Ищет для иностранных фильмов их запись на IMDb.
Результат записывает в базу SQLite.

  ```
  ./parse_ratings.py ./user_5555555.html my_kinopoisk_ratings.db
