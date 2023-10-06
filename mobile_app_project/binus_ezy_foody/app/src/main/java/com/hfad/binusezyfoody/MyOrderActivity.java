package com.hfad.binusezyfoody;

import androidx.appcompat.app.AppCompatActivity;
import androidx.recyclerview.widget.DefaultItemAnimator;
import androidx.recyclerview.widget.DividerItemDecoration;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

import android.content.Context;
import android.content.Intent;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.TextView;
import android.widget.Toast;

import java.io.Serializable;
import java.util.ArrayList;

public class MyOrderActivity extends AppCompatActivity {
    private static ArrayList<MyOrder> myOrderList = new ArrayList<>();
    private RecyclerView recyclerViewMyOrder;
    private TextView emptyText;
    private TextView totalPriceText;
    private Button payNowBtn;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_my_order);

//        myOrderList = new ArrayList<>();
//
////        Types:
////        Drink
////        Snack
////        Food
//
//        myOrderList.add(new MyOrder("Air Mineral", 3000, 2, R.drawable.air_mineral));
//        myOrderList.add(new MyOrder("Tempe Goreng", 1000, 3, R.drawable.tempe_goreng));

        emptyText = findViewById(R.id.emptyOrderText);
        totalPriceText = findViewById(R.id.totalPriceText);
        payNowBtn = findViewById(R.id.payNowBtn);

        recyclerViewMyOrder = findViewById(R.id.myOrderList);
        recyclerAdapterMyOrder adapter = new recyclerAdapterMyOrder(myOrderList);
        RecyclerView.LayoutManager layoutManager = new LinearLayoutManager(getApplicationContext());
        recyclerViewMyOrder.setLayoutManager(layoutManager);
        recyclerViewMyOrder.setItemAnimator(new DefaultItemAnimator());
        recyclerViewMyOrder.setAdapter(adapter);
        recyclerViewMyOrder.addItemDecoration(new DividerItemDecoration(recyclerViewMyOrder.getContext(), DividerItemDecoration.VERTICAL));

        if (adapter.getItemCount() != 0) {
            recyclerViewMyOrder.setVisibility(View.VISIBLE);
            emptyText.setVisibility(View.GONE);
            totalPriceText.setText("Total: Rp " + adapter.getTotalPrice());
            payNowBtn.setEnabled(true);
        }else{
            recyclerViewMyOrder.setVisibility(View.GONE);
            emptyText.setVisibility(View.VISIBLE);
            totalPriceText.setText("Total: Rp 0");
            payNowBtn.setEnabled(false);
        }

    }

    public void payNowOnclick(View view) {
        Intent intent = new Intent(this, OrderCompleteActivity.class);
        intent.putExtra("success", 1);

//        Bundle bundle = new Bundle();
//        bundle.putSerializable("myOrderList", (Serializable) myOrderList);
//
//        intent.putExtra("Bundle", bundle);

        startActivity(intent);
    }

    public void backOnclick(View view) {
        finish();
    }

    public static ArrayList<MyOrder> getMyOrderList() { return myOrderList; }

    public static void clearMyOrder() {
        myOrderList.clear();
    }

}