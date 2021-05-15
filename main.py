from pymongo import MongoClient
import requests
import re
import os
from bs4 import BeautifulSoup
import datetime
import dateparser



def main():
    client = MongoClient('localhost', 27017)
    db = client.library
    coll_book = db.books
    coll_author = db.author


    while True:

        os.system("cls")

        print("1) Добавить книгу \n"
              "2) Добавить автора \n"
              "3) Добавить все книги одного автора \n"
              "4) Вывести краткое описание книги \n"
              "5) Отсортировать книги по названию \n"
              "6) Посчитать количество повторяющихся фамилий у авторов \n"
              "7) Вывести названия всех жанров \n"
              "8) Количество книг одного автора \n"
              "9) Удалить одну книгу \n"
              "10) Удалить всю коллекцию \n"
              "11) Выход")

        com = input()

        if com == '1':
            print("Введите ссылку на книгу с сайта www.litres.ru")
            url = input()
            try:
                book = book_data(url)
            except:
                print('Ошибка при парсинге страницы')
            else:
                if book == -1:
                    print("Error: can't connect to url")

                book_id = coll_book.insert_one(book).inserted_id
        elif com == '2':
            print("Введите ссылку на автора с сайта www.litmir.me")
            url = input()
            try:
                author = get_author_info(url)
            except:
                print('Ошибка при парсинге страницы')
            else:
                if author == -1:
                    print("Error: can't connect to url")

                if author == "Error: wrong url!":
                    print("Error: wrong url!")
                    continue

                author["books"] = []

                book_id = coll_author.insert_one(author).inserted_id

        elif com == '3':
            print("Введите ссылку на автора с сайта www.litres.ru")
            url = input()
            try:
                author, all_books = get_books_by_author(url)
            except:
                print('Ошибка при парсинге страницы')
            else:
                if all_books == -1:
                    print("Error: can't connect to url")

                ar = author.split(" ")

                if len(ar) < 2:
                    print('Ошибка при обработке автора на этой странице')
                    continue

                first_name = ar[0]
                second_name = ar[1]

                if coll_author.count_documents({'first_name':first_name, 'last_name':second_name}) > 0:
                    coll_author.find_one_and_update({'first_name': first_name, 'last_name': second_name},
                                                    {"$set": {'books': all_books}})
                else:
                    print("Данного автора нет в коллекции")

        elif com == "4":
            print("Введите название книги")
            name_book = input()

            desc = coll_book.find_one({"title": name_book}, {"description": 1})
            if desc is not None:
                print(desc["description"])
            else:
                print("Данной книги не существует")

        elif com == "5":
            print("Введите 1, если хотите отсортировать от A до Z и от А до Я или введите -1, если хотите отсортировать наоборот")
            value_sort = input()

            try:
                if int(value_sort) == 1 or int(value_sort) == -1:
                    result_sort = coll_book.find({},{"title": 1}).sort("title", int(value_sort))
                    for document in result_sort:
                        print(document["title"])
                else:
                    print("Вы специально ввели не то число?")
            except ValueError:
                print("Смешно, это ж даже не число")


        elif com == "6":
            print("Введите фамилию автора")
            fam_author = input()

            author_count = coll_author.count_documents({"last_name": fam_author})
            if author_count != 0:
                print(author_count)
            else:
                print("Такой фамилии автора не существует")

        elif com == "7":
            name_all_genre = coll_book.distinct("genre")
            for name in name_all_genre:
                print(name)

        elif com == "8":
            print("Введите имя и фамилию автора")
            name_author = input()

            result = coll_book.aggregate([{"$match": {"author": name_author}}, {"$group": {"_id": "$author", "count": {"$sum": 1}}}])
            for res in result:
                print(res)

        elif com == "9":
            print("Введите название книги")
            name = input()

            remove = coll_book.delete_one({"title" : name})
            if remove.deleted_count != 0:
                print("Книга удалена")
            else:
                print("Такой книги не существует")

        elif com == "10":
            delete_all = coll_author.delete_many({})

        elif com == "11":
            break


def book_data(url):
    try:
        r = requests.get(url)
    except:
        print("Error: can't connect to this url")
        return -1

    soup = BeautifulSoup(r.content, "html.parser")

    title = soup.find("div", {"class": "biblio_book_name biblio-book__title-block"}).contents[0].contents[0]
    author = soup.find("a", {"class": "biblio_book_author__link"}).contents[0]

    genre = soup.find_all("a", {"class": "biblio_info__link"})

    genre_name = genre[0].contents[0].contents[0] + genre[0].contents[1]

    description = soup.find("div", {"class": "biblio_book_descr_publishers"})
    full_description = ''

    if description is not None:
        parts = description.contents

        for part in parts:
            if len(part.contents) != 0:
                if str(type(part.contents[0])) == "<class 'bs4.element.NavigableString'>":
                    full_description += '\n' + part.contents[0]
                else:
                    full_description = ''



    book = {'title': title, 'author': author, 'genre': genre_name, 'description': full_description}
    print(book)

    return book


def get_author_info(url):
    try:
        r = requests.get(url)
    except:
        print("Error: can't connect to this url")
        return -1

    soup = BeautifulSoup(r.content, "html.parser")

    _fullname = soup.find("div", {"class": "lt35"})
    if _fullname is None:
        return "Error: wrong url!"

    fullname = _fullname.contents[0].contents[0]

    ar = fullname.split(" ")
    ar.pop(0)
    ar.pop(len(ar) - 1)
    print(ar)

    name = ar[1]
    last_name = ar[0]
    patronymic = ""

    if len(ar) == 3:
        patronymic = ar[2]

    birthday = soup.find("span", {"itemprop": "birthDate"}).contents[0]

    if soup.find("span", {"itemprop": "deathDate"}) == None:
        death_date = ''
    else:
        death_date = soup.find("span", {"itemprop": "deathDate"}).contents[0]

    #d = dateparser.parse(birthday)

    author = {
        "first_name": name,
        "last_name": last_name,
        "patronymic": patronymic,
        "birthday": birthday,
        "death_date": death_date
    }

    return author

def get_books_by_author(url):
    try:
        r = requests.get(url)
    except:
        print("Error: can't connect to this url a")
        return -1

    soup = BeautifulSoup(r.content, "html.parser")
    links = soup.find_all("a", {"class": "art_name_link"})

    books = []
    titles = []

    author = ""
    for link in links:
        r = re.compile("[а-яА-Я]+")

        if len(link.contents[0].contents) == 1 or str(
                type(link.contents[0].contents[1])) == "<class 'bs4.element.Tag'>":
            match = re.match(r, link.contents[0].contents[0])
        else:
            match = re.match(r, link.contents[0].contents[1])

        if bool(match):
            book = book_data("https://www.litres.ru" + link.get("href"))

            if book['title'] not in titles:
                if author == "":
                    author = book['author']

                book.pop('author')
                books.append(book)
                titles.append(book['title'])

    return author, books


if __name__ == "__main__":
    main()