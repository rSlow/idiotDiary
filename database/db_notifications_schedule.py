import sqlite3 as sql

__all__ = ("get_user_data",
           "get_all_notifications",
           "enable_notifications",
           "disable_notifications",
           "add_user",
           "db",
           "set_group_to_user",
           "set_time_to_user",
           )


def get_user_data(user_id):
    cursor = db.cursor()
    res = cursor.execute("select * from notifications where "
                         "id=?",
                         (user_id,)).fetchone() or ()
    cursor.close()
    return res


def get_all_notifications():
    cursor = db.cursor()
    res = cursor.execute("select * from notifications where "
                         "notifications=1 and time!=''").fetchall()
    cursor.close()
    return res


def enable_notifications(user_id):
    cursor = db.cursor()
    cursor.execute("update notifications set notifications=?"
                   "where id=?",
                   (True, user_id))
    cursor.close()
    db.commit()


def disable_notifications(user_id):
    cursor = db.cursor()
    cursor.execute("update notifications set notifications=0 where id=?",
                   (user_id,))
    cursor.close()
    db.commit()


def add_user(user_id):
    cursor = db.cursor()
    cursor.execute("insert into notifications values (?, 0, '', '[]')",
                   (user_id,))
    cursor.close()
    db.commit()


def set_group_to_user(group, user_id):
    cursor = db.cursor()
    cursor.execute("update notifications set user_group=? where id=?",
                   (group, user_id))
    cursor.close()
    db.commit()


def set_time_to_user(time_str, user_id):
    cursor = db.cursor()
    cursor.execute("update notifications set time=? where id=?",
                   (time_str, user_id))
    cursor.close()
    db.commit()


db = sql.connect("databases/bot_database.db")
# cursor = db.cursor()
db.execute('create table if not exists notifications('
           'id integer primary key unique ,'
           'notifications boolean default false ,'
           'user_group text ,'
           'time text)')
db.commit()
