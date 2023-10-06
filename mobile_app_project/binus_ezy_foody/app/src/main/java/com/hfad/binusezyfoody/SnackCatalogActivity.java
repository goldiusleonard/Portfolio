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

public class SnackCatalogActivity extends AppCompatActivity {
    private static ArrayList<Snack> snackList;
    private RecyclerView recyclerViewSnack;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_snack_catalog);

        snackList = new ArrayList<>();

        snackList.add(new Snack("Tempe Goreng", 1000, R.drawable.tempe_goreng));
        snackList.add(new Snack("Tahu Goreng", 1000, R.drawable.tahu_goreng));
        snackList.add(new Snack("Risol", 5000, R.drawable.risol));
        snackList.add(new Snack("Pisang Goreng", 5000, R.drawable.pisang_goreng));
        snackList.add(new Snack("Tempe Mendoan", 7000, R.drawable.tempe_mendoan));
        snackList.add(new Snack("Singkong Krispi", 3000, R.drawable.singkong_krispi));
        snackList.add(new Snack("Jamur Krispi", 10000, R.drawable.jamur_krispi));

        recyclerViewSnack = findViewById(R.id.snackList);
        recyclerAdapterSnack adapter = new recyclerAdapterSnack(snackList);
        RecyclerView.LayoutManager layoutManager = new LinearLayoutManager(getApplicationContext());
        recyclerViewSnack.setLayoutManager(layoutManager);
        recyclerViewSnack.setItemAnimator(new DefaultItemAnimator());
        recyclerViewSnack.setAdapter(adapter);
        recyclerViewSnack.addItemDecoration(new DividerItemDecoration(recyclerViewSnack.getContext(), DividerItemDecoration.VERTICAL));
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

    public static Snack getSnack(int pos) { return snackList.get(pos); }

}