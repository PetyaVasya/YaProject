# _COPAI_
+ [Мысли](#Start);
+ [Техническое задание](#tech-job);
+ [Итог](#result);
+ [Все для старта](#launch).  
<a name="Start"></a>
Темные времена настали и в интернете, человек окружен тысячами информационных ресурсов,
и каждый манит тебя своими лозунгами и SEO-маркетингом на 5 строчках в яндексе выдаче.  
Мир погряз в хаосе, пока не вернулись они, старейшины, обладающие затерянными руническими
символами - Языком запросов. Казалось бы все, вот те кто воспитает новых героев и научит
их не кликать на первую ссылку в выдаче, ведь это реклама, те кто объяснит, что wikipedia
это собирательный образ, а не достоверный источник, те кто объяснит, что ничего в мире не найти на
кирилице, потому что вся техническая литература на латинице, но нет передоз информации охватил
и мудрецов. Как же собрать названия всех котиков с сайта, а также их окрас, вид шерсти, как
получить все предложения с Avito в удобной Excel таблицы о новой видеокарте для запуска
Ведьмака на ультрах, а как найти всех Жень в вк и поздравить их с днем рождения лично?  
Ладно не будем таить, парсер, просто парсер. Да, да, та самая программа для сбора информации в вебе,
эти пауки прочесывают все, арахнофобы держитесь, возможно ваши лыжи с балкона, которые вы выставили
за 3500, уже облюбовала парочка таких.  
Хотя, господи, вы когда-нибудь слышали, что такое безумие? Так это писать несколько парсеров,
они все как на одно лицо, эти чертовы requests.get повсюду, и только мизер данных отличается,
пара селекторов, один класс искомого объекта.
<a name="tech-job"></a>
### Техническое задание
Недавно мы основали отдел продаж, к нам пришел один умный парень, но доверчивый парень,
он решил возглавить разработку одного проекта, за что был сразу же уволен, экая дерзость,
однако его идея не последовала примеру её хозяина и прижилась. Выводы делайте сами.  
Задача была изложена следующим образом:
`необходимо разработать, кхм, кхм, конструктор парсеров да бы упростить монотонный процесс
дублирования кода, от сайта к сайту, оставив лишь то, что действительно меняется,
а именно: селекторы`.  
А что из этого вышло, читайте буквально через одну строку.
<a name="result"></a>
### Итог
Поздравляем вас с приобретением полной версии файла [readme.md](./readme.md).  
Вам повезло, несмотря что идея не нова, но платить по 50$ в месяц или 250$, а иногда и 500$,
не каждому захочется. Поэтому вашему вниманию представляется самодельный конструктор парсеров.
Совершенно бесплатно. Он совмещает в себе плюсы плагинов для браузеров и плюсы десктопным
приложений. Вот он проект, кототко названный COPAI(**C**onstructor **O**f **P**arsers by **I**sqK).
Вы можете создавать несколько парсеров и не просто указывать необходимые поля в слепую, а можете
интерактивно выбирать их во встроенном окне бразуера, правдо после 5 обновления QT, оно работает
нестабильно, но подождем обновлений, возможно QTWebEngineView выйдет на уровень старого браузерного
окна, и баги с ним пофиксятся, а мы избавимся от костылей.  
Также помимо простого указывания ссылок, вы можете получить sitemap(карту сайта) и указывать
необходимые вам разделы сайта, нужные для парсинга.  
Также можно указать список прокси, чтобы на душе проще было  
А затем получить результат в excel файле
<a name="launch"></a>
### Все для старта
Для запуска приложения многого и не нужно, только установить все библиотеки из
[requirements.txt](./requirements.txt). Возможно у вас не встанет lxml на Windows 10, тогда
воспользуйтесь html5lib и замените "lxml" на "html5lib" в файле [Parser.py](./Parser.py)  
Однако дальше вас ждет ряд очевидных ограничей и лишений. Данный парсер не может работать с сайтами
с онлайн подгрузкой данных, т.е. через JS, а также с данными указанными в iframe, для их парсинга
вам нужно будет указать прямую ссылку на ресурс. Также парсер обходит блокировки лишь при
помощи прокси, так что их стоит использовать, иначе вы вряд ли найдете любимую видеокарту на авито  
Также не все поля имеют уникальные селекторы из их класса и id, поэтому используйте не только
Left Click на элементе, но и Shift+Left Click для получения полного пути до элемента.  
Получение файлов Sitemap сайта долгий и трудоемкий процесс, т.к. например avito располагает огромной
товарной базой, так что этот процесс займет несколько часов, поэтому не спешите закрывать программу  
Также TreeWidget в QT отъедает очень много ресурсов, поэтому на больших сайтах он будет
неизбежно лагать, хоть мы и постаралсь оптимизировать файлы sitemap у сайтов.  
В качестве селекторов для указания полей используется
[XPATH](https://www.w3schools.com/xml/xpath_syntax.asp). Если какой-то селектор не работает при
автоматическом составлении, придется воспользоваться данным гайдом.
Помните, что на Windows 10 интерфейс, как всегда ужасен, действительно, зачем красивый интерфейс
на OS, базирующейся на интерфейсе пользователя, ну что поделать. Эти прогресс бары не улучшить.  
После парсинга вы получите excel файл, а если скачали файл sitemap, то и его в придачу,
со всеми ссылками сайта, однако некоторые сайты, могут не распологать ими,
что редкость в наше время.  
Для ваше удобства, предоставляем вам некогда активную базу для примера, возможно что-то поменялось,
а что никогда и не работало, мы не углублялись в проверки и все это было баловство, но надеемся,
что это вам как-то поможет