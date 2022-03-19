import sqlite3 as sql

__all__ = ("add_new_user",
           "get_all_users",
           "deactivate_user",
           )


def add_new_user(user_obj):
    cursor = db.cursor()
    user_id = user_obj.id
    user_full_name = user_obj.full_name
    username = user_obj.mention
    cursor.execute("insert into main_table values (?,?,?,?)",
                   (user_id, user_full_name, username, True))
    cursor.close()
    db.commit()


def get_all_users():
    cursor = db.cursor()
    users_data = cursor.execute("select * from main_table").fetchall()
    ids = [user_data[0] for user_data in users_data]
    cursor.close()
    return ids


def deactivate_user(user_id):
    cursor = db.cursor()
    cursor.execute("update main_table set active=false where id=?",
                   (user_id,))
    cursor.close()
    db.commit()


db = sql.connect("databases/bot_database.db")
db.execute('create table if not exists main_table('
           'id integer primary key unique,'
           'full_name blob,'
           'username text,'
           'active boolean default true)')
db.commit()
