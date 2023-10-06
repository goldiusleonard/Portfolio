package com.hfad.binusezyfoody;

import androidx.appcompat.app.AppCompatActivity;

import android.content.Intent;
import android.graphics.drawable.Drawable;
import android.os.Bundle;
import android.view.View;

import java.io.Serializable;
import java.util.ArrayList;

public class MainActivity extends AppCompatActivity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

    }

    public void myOrderOnclick(View view) {
        Intent intent = new Intent(this, MyOrderActivity.class);
        startActivity(intent);
    }

    public void drinkOnclick(View view) {
        Intent intent = new Intent(this, DrinkCatalogActivity.class);
        startActivity(intent);
    }

    public void snackOnclick(View view) {
        Intent intent = new Intent(this, SnackCatalogActivity.class);
        startActivity(intent);
    }

    public void foodOnclick(View view) {
        Intent intent = new Intent(this, FoodCatalogActivity.class);
        startActivity(intent);
    }

    public void topupOnclick(View view) {
        startActivity(new Intent(this, TopUpActivity.class));
    }

}