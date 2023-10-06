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

public class FoodCatalogActivity extends AppCompatActivity {
    private static ArrayList<Food> foodList;
    private RecyclerView recyclerViewFood;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_food_catalog);

        foodList = new ArrayList<>();

        foodList.add(new Food("Indonesian Mie", 7000, R.drawable.indonesian_mie));
        foodList.add(new Food("Coto Makassar", 15000, R.drawable.coto_makassar));
        foodList.add(new Food("Sate Padang", 25000, R.drawable.sate_padang));
        foodList.add(new Food("Nasi Uduk", 8000, R.drawable.nasi_uduk));
        foodList.add(new Food("Nasi Goreng", 13000, R.drawable.nasi_goreng));
        foodList.add(new Food("Bakso Malang", 20000, R.drawable.bakso_malang));
        foodList.add(new Food("Kwetiau Goreng", 15000, R.drawable.kwetiau_goreng));

        recyclerViewFood = findViewById(R.id.foodList);
        recyclerAdapterFood adapter = new recyclerAdapterFood(foodList);
        RecyclerView.LayoutManager layoutManager = new LinearLayoutManager(getApplicationContext());
        recyclerViewFood.setLayoutManager(layoutManager);
        recyclerViewFood.setItemAnimator(new DefaultItemAnimator());
        recyclerViewFood.setAdapter(adapter);
        recyclerViewFood.addItemDecoration(new DividerItemDecoration(recyclerViewFood.getContext(), DividerItemDecoration.VERTICAL));
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

    public static Food getFood(int pos) { return foodList.get(pos); }

}