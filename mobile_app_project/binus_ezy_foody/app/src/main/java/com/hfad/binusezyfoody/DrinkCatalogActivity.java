package com.hfad.binusezyfoody;

import androidx.appcompat.app.AppCompatActivity;
import androidx.recyclerview.widget.DefaultItemAnimator;
import androidx.recyclerview.widget.DividerItemDecoration;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

import android.content.Intent;
import android.os.Bundle;
import android.view.View;

import java.util.ArrayList;

public class DrinkCatalogActivity extends AppCompatActivity {
    private static ArrayList<Drink> drinkList;
    private RecyclerView recyclerViewDrink;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_drink_catalog);
        drinkList = new ArrayList<>();

        drinkList.add(new Drink("Air Mineral", 3000, R.drawable.air_mineral));
        drinkList.add(new Drink("Jus Apel", 12000, R.drawable.jus_apel));
        drinkList.add(new Drink("Jus Mangga", 15000, R.drawable.jus_mangga));
        drinkList.add(new Drink("Jus Alpukat", 18000, R.drawable.jus_alpukat));
        drinkList.add(new Drink("Jus Jambu", 20000, R.drawable.jus_jambu));
        drinkList.add(new Drink("Es Teh Tawar", 5000, R.drawable.es_teh_tawar));
        drinkList.add(new Drink("Teh Tawar", 4000, R.drawable.teh_tawar));

        recyclerViewDrink = findViewById(R.id.DrinkList);
        recyclerAdapterDrink adapter = new recyclerAdapterDrink(drinkList);
        RecyclerView.LayoutManager layoutManager = new LinearLayoutManager(getApplicationContext());
        recyclerViewDrink.setLayoutManager(layoutManager);
        recyclerViewDrink.setItemAnimator(new DefaultItemAnimator());
        recyclerViewDrink.setAdapter(adapter);
        recyclerViewDrink.addItemDecoration(new DividerItemDecoration(recyclerViewDrink.getContext(), DividerItemDecoration.VERTICAL));
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

    public void backOnclick(View view) {
        finish();
    }

    public static Drink getDrink(int pos) { return drinkList.get(pos); }
}