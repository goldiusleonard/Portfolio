package com.hfad.binusezyfoody;

import androidx.appcompat.app.AppCompatActivity;

import android.content.Intent;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.ImageView;
import android.widget.TextView;

import java.util.ArrayList;

public class updateMyOrderActivity extends AppCompatActivity {
    private TextView nameText;
    private TextView priceText;
    private TextView quantityText;
    private ImageView imgView;
    private String type;
    private Integer position;
    private Integer price;
    private Integer quantity;
    private Button removeBtn;
    private Button addBtn;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_update_my_order);

        removeBtn = findViewById(R.id.removeMyOrderBtn);
        addBtn = findViewById(R.id.addMyOrderBtn);

        Intent intent = getIntent();
        String name = intent.getStringExtra("name");
        price = intent.getIntExtra("price", 0);
        int img = intent.getIntExtra("img", 0);

        position = intent.getIntExtra("position", 0);
        type = intent.getStringExtra("type");
        quantity = 0;

        ArrayList<MyOrder> myOrderList = new ArrayList<>(MyOrderActivity.getMyOrderList());
        int size = myOrderList.size();

        for(int i = 0; i < size; i++) {
            MyOrder order = myOrderList.get(i);
            if(type.equals(order.getType()) && position == order.getPosition()) {
                quantity = order.getQuantity();
                break;
            }
        }

        nameText = findViewById(R.id.name);
        priceText = findViewById(R.id.price);
        imgView = findViewById(R.id.product_img);
        quantityText = findViewById(R.id.quantity);

        if(quantity == 0) {
            removeBtn.setEnabled(false);
            priceText.setText(price.toString());
        }
        else {
            removeBtn.setEnabled(true);
            Integer subTotalPrice = price * quantity;
            priceText.setText(subTotalPrice.toString());
        }

        nameText.setText(name);
        quantityText.setText("Qty: " + quantity.toString());
        imgView.setImageResource(img);
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

    public void removeItemOnclick(View view) {
        quantity -= 1;

        if(quantity == 0) {
            removeBtn.setEnabled(false);
            priceText.setText(price.toString());
            quantityText.setText("Qty: " + quantity.toString());
        }
        else {
            removeBtn.setEnabled(true);
            Integer subTotalPrice = price * quantity;
            priceText.setText(subTotalPrice.toString());
            quantityText.setText("Qty: " + quantity.toString());
        }

    }

    public void addItemOnclick(View view) {
        quantity += 1;

        if(quantity == 0) {
            removeBtn.setEnabled(false);
            priceText.setText(price.toString());
            quantityText.setText("Qty: " + quantity.toString());
        }
        else {
            removeBtn.setEnabled(true);
            Integer subTotalPrice = price * quantity;
            priceText.setText(subTotalPrice.toString());
            quantityText.setText("Qty: " + quantity.toString());
        }
    }

    public void confirmOnclick(View view) {
        ArrayList<MyOrder> myOrderList = MyOrderActivity.getMyOrderList();
        int size = myOrderList.size();
        int exist = 0;

        for(int i = 0; i < size; i++) {
            MyOrder order = myOrderList.get(i);
            if(type.equals(order.getType()) && position == order.getPosition()) {
                if(quantity > 0) {
                    order.setQuantity(quantity);
                    myOrderList.set(i, order);
                }
                else {
                    myOrderList.remove(i);
                }

                exist = 1;
                break;
            }
        }

        if(exist == 0 && quantity > 0) {
            myOrderList.add(new MyOrder(type, position, quantity));
        }

        startActivity(new Intent(this, MyOrderActivity.class));
    }

    public void backOnclick(View view) {
        finish();
    }

}