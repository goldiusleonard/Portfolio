package com.hfad.binusezyfoody;

import androidx.appcompat.app.AppCompatActivity;
import androidx.recyclerview.widget.DefaultItemAnimator;
import androidx.recyclerview.widget.DividerItemDecoration;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

import android.content.Intent;
import android.os.Bundle;
import android.view.View;
import android.widget.TextView;

import java.util.ArrayList;

public class OrderCompleteActivity extends AppCompatActivity {
    private TextView totalPriceText;
    private TextView orderCompleteText;
    private RecyclerView recyclerViewOrderComplete;
    private ArrayList<MyOrder> myOrderList;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_order_complete);

        Intent intent = getIntent();
//        Bundle args = intent.getBundleExtra("Bundle");
//        ArrayList<MyOrder> myOrderList = (ArrayList<MyOrder>) args.getSerializable("myOrderList");

        int success = intent.getIntExtra("success", 0);

        orderCompleteText = findViewById(R.id.order_complete);

        if(success == 1) {
            orderCompleteText.setText("Your order complete.\nThank You");
        }
        else {
            orderCompleteText.setText("Sorry,\nyour order failed");
        }

        totalPriceText = findViewById(R.id.totalPriceText);

        myOrderList = new ArrayList<>(MyOrderActivity.getMyOrderList());

        recyclerViewOrderComplete = findViewById(R.id.myCompleteOrderList);
        recyclerAdapterCompleteOrder adapter = new recyclerAdapterCompleteOrder(myOrderList);
        RecyclerView.LayoutManager layoutManager = new LinearLayoutManager(getApplicationContext());
        recyclerViewOrderComplete.setLayoutManager(layoutManager);
        recyclerViewOrderComplete.setItemAnimator(new DefaultItemAnimator());
        recyclerViewOrderComplete.setAdapter(adapter);
        recyclerViewOrderComplete.addItemDecoration(new DividerItemDecoration(recyclerViewOrderComplete.getContext(), DividerItemDecoration.VERTICAL));

        recyclerViewOrderComplete.setVisibility(View.VISIBLE);
        totalPriceText.setText("Total: Rp " + adapter.getTotalPrice());
        MyOrderActivity.clearMyOrder();
    }

    public void myOrderOnclick(View view) {
        startActivity(new Intent(this, MyOrderActivity.class));
    }

    public void drinkOnclick(View view) {
        startActivity(new Intent(this, DrinkCatalogActivity.class));
    }

    public void snackOnclick(View view) {
        startActivity(new Intent(this, SnackCatalogActivity.class));
    }

    public void foodOnclick(View view) {
        startActivity(new Intent(this, FoodCatalogActivity.class));
    }

    public void homeOnclick(View view) {
        startActivity(new Intent(this, MainActivity.class));
    }
}