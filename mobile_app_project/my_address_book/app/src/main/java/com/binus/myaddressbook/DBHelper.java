package com.binus.myaddressbook;

import android.content.ContentValues;
import android.content.Context;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.database.sqlite.SQLiteOpenHelper;

import androidx.annotation.Nullable;

public class DBHelper extends SQLiteOpenHelper {
    public DBHelper(Context context) {
        super(context, "address_book.db", null, 1);
    }

    @Override
    public void onCreate(SQLiteDatabase db) {
        db.execSQL("CREATE TABLE AddressBooks(id TEXT PRIMARY KEY, first TEXT, last TEXT, city TEXT, country TEXT, phone TEXT, cell TEXT, email TEXT, image_path TEXT)");
    }

    @Override
    public void onUpgrade(SQLiteDatabase db, int oldVersion, int newVersion) {
        db.execSQL("DROP TABLE IF EXISTS AddressBooks");
    }

    public Boolean insertData(String id, String first, String last, String city, String country, String phone, String cell, String email, String image_path) {
        SQLiteDatabase db = this.getWritableDatabase();
        ContentValues contentValues = new ContentValues();
        contentValues.put("id", id);
        contentValues.put("first", first);
        contentValues.put("last", last);
        contentValues.put("city", city);
        contentValues.put("country", country);
        contentValues.put("phone", phone);
        contentValues.put("cell", cell);
        contentValues.put("email", email);
        contentValues.put("image_path", image_path);
        long result = db.insert("AddressBooks", null, contentValues);
        if (result == -1) {
            return false;
        }
        else {
            return true;
        }
    }

    public Boolean deleteData(String id) {
        SQLiteDatabase db = this.getWritableDatabase();
        Cursor cursor = db.rawQuery("SELECT * FROM AddressBooks WHERE id = ?", new String[] {id});
        if (cursor.getCount() > 0) {
            long result = db.delete("AddressBooks", "id=?", new String[] {id});
            if (result == -1) {
                return false;
            }
            else {
                return true;
            }
        }
        else {
            return false;
        }
    }

    public Cursor getData() {
        SQLiteDatabase db = this.getWritableDatabase();
        Cursor cursor = db.rawQuery("SELECT * FROM AddressBooks", null);
        return cursor;
    }

}
